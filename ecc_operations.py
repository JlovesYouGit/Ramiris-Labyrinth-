"""
Refactored ECC Operations Module

Provides clean, modular elliptic curve operations for secp256k1.
Separated from the main authentication logic for better maintainability.
"""

import hashlib
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

from authentication_interface import AuthenticationConfig, AuthenticationLogger, AuthenticationResult


@dataclass
class CurvePoint:
    """Represents a point on the elliptic curve."""
    x: int
    y: int
    is_infinity: bool = False
    
    def __str__(self):
        if self.is_infinity:
            return "Point at infinity"
        return f"({hex(self.x)[:20]}..., {hex(self.y)[:20]}...)"
    
    def __eq__(self, other):
        if not isinstance(other, CurvePoint):
            return False
        if self.is_infinity and other.is_infinity:
            return True
        if self.is_infinity or other.is_infinity:
            return False
        return self.x == other.x and self.y == other.y


class Secp256k1Curve:
    """
    Optimized secp256k1 elliptic curve implementation.
    
    Curve equation: y² = x³ + 7 (mod p)
    Used by Bitcoin for digital signatures.
    """
    
    def __init__(self, config: AuthenticationConfig = None):
        self.config = config or AuthenticationConfig()
        self.logger = AuthenticationLogger("ecc_operations")
        
        # Load curve parameters
        params = self.config.get_config("secp256k1")
        self.p = params['p']
        self.a = params['a'] 
        self.b = params['b']
        self.g = CurvePoint(params['gx'], params['gy'])
        self.n = params['n']
        
        # Pre-computed values for optimization
        self._precompute_multiples()
        
        self.logger.log_success("ECC curve initialized", f"secp256k1 with order n={hex(self.n)[:30]}...")
    
    def _precompute_multiples(self, window_size: int = 4):
        """Pre-compute multiples of generator point for faster scalar multiplication."""
        self.window_size = window_size
        self.precomputed = {}
        
        # Pre-compute G, 2G, 4G, 8G, ... for windowed multiplication
        current = self.g
        for i in range(2 ** window_size):
            self.precomputed[i] = current
            current = self.point_add(current, self.g)
    
    def is_on_curve(self, point: CurvePoint) -> bool:
        """Check if a point lies on the curve."""
        if point.is_infinity:
            return True
        
        left = (point.y * point.y) % self.p
        right = (point.x * point.x * point.x + self.a * point.x + self.b) % self.p
        return left == right
    
    def point_add(self, p: Optional[CurvePoint], q: Optional[CurvePoint]) -> Optional[CurvePoint]:
        """Add two points on the elliptic curve."""
        if p is None or p.is_infinity:
            return q
        if q is None or q.is_infinity:
            return p
        
        # Check if points are equal (for point doubling)
        if p.x == q.x:
            if p.y == q.y:
                return self.point_double(p)
            else:
                # P + (-P) = point at infinity
                return CurvePoint(0, 0, is_infinity=True)
        
        # Calculate slope: m = (y2 - y1) / (x2 - x1) mod p
        numerator = (q.y - p.y) % self.p
        denominator = (q.x - p.x) % self.p
        denominator_inv = pow(denominator, -1, self.p)
        m = (numerator * denominator_inv) % self.p
        
        # Calculate result point
        x3 = (m * m - p.x - q.x) % self.p
        y3 = (m * (p.x - x3) - p.y) % self.p
        
        return CurvePoint(x3, y3)
    
    def point_double(self, p: CurvePoint) -> Optional[CurvePoint]:
        """Double a point on the elliptic curve."""
        if p.is_infinity:
            return p
        
        # Calculate slope: m = (3*x² + a) / (2*y) mod p
        numerator = (3 * p.x * p.x + self.a) % self.p
        denominator = (2 * p.y) % self.p
        denominator_inv = pow(denominator, -1, self.p)
        m = (numerator * denominator_inv) % self.p
        
        # Calculate result point
        x3 = (m * m - 2 * p.x) % self.p
        y3 = (m * (p.x - x3) - p.y) % self.p
        
        return CurvePoint(x3, y3)
    
    def scalar_multiply(self, k: int, p: CurvePoint = None) -> Optional[CurvePoint]:
        """
        Scalar multiplication: k * P using windowed method.
        
        Args:
            k: Scalar multiplier
            p: Point to multiply (defaults to generator G)
            
        Returns:
            Result point or None if invalid
        """
        if p is None:
            p = self.g
        
        if k % self.n == 0 or p.is_infinity:
            return CurvePoint(0, 0, is_infinity=True)
        
        # Use windowed method for optimization
        result = CurvePoint(0, 0, is_infinity=True)
        
        # Process scalar in windows
        window_size = self.window_size
        window_mask = (1 << window_size) - 1
        
        for i in range(0, 256, window_size):
            window_value = (k >> i) & window_mask
            
            if window_value != 0:
                # Add pre-computed point
                precomputed_point = self.precomputed.get(window_value, self.g)
                # Need to multiply by 2^i
                scaled_point = self._multiply_by_power_of_two(precomputed_point, i)
                result = self.point_add(result, scaled_point)
        
        return result
    
    def _multiply_by_power_of_two(self, point: CurvePoint, power: int) -> CurvePoint:
        """Multiply point by 2^power using repeated doubling."""
        result = point
        for _ in range(power):
            result = self.point_double(result)
        return result
    
    def point_negate(self, p: CurvePoint) -> CurvePoint:
        """Negate a point on the curve."""
        if p.is_infinity:
            return p
        return CurvePoint(p.x, (-p.y) % self.p)
    
    def compress_point(self, point: CurvePoint) -> bytes:
        """Compress a point to 33 bytes."""
        if point.is_infinity:
            return b'\x00'
        
        prefix = b'\x03' if point.y % 2 == 1 else b'\x02'
        x_bytes = point.x.to_bytes(32, 'big')
        return prefix + x_bytes
    
    def decompress_point(self, compressed: bytes) -> Optional[CurvePoint]:
        """Decompress a point from 33 bytes."""
        if len(compressed) != 33:
            return None
        
        prefix = compressed[0]
        x_bytes = compressed[1:]
        x = int.from_bytes(x_bytes, 'big')
        
        # Calculate y from curve equation: y² = x³ + 7
        y_squared = (pow(x, 3, self.p) + 7) % self.p
        y = pow(y_squared, (self.p + 1) // 4, self.p)
        
        # Adjust y based on prefix
        if (prefix == 0x03 and y % 2 == 0) or (prefix == 0x02 and y % 2 == 1):
            y = (-y) % self.p
        
        return CurvePoint(x, y)
    
    def get_curve_info(self) -> Dict[str, Any]:
        """Get comprehensive curve information."""
        return {
            "curve_name": "secp256k1",
            "field_size": self.p,
            "curve_order": self.n,
            "generator": str(self.g),
            "coefficient_a": self.a,
            "coefficient_b": self.b,
            "security_bits": 256,
            "window_size": self.window_size,
            "precomputed_points": len(self.precomputed)
        }


class ECCKeyPair:
    """Represents an ECC key pair with validation and conversion methods."""
    
    def __init__(self, private_key_int: int, curve: Secp256k1Curve):
        self.curve = curve
        self.private_key = private_key_int
        self.public_key = curve.scalar_multiply(private_key_int)
        
        # Cache derived values
        self._public_key_compressed = None
        self._public_key_uncompressed = None
        self._address = None
    
    @property
    def public_key_compressed(self) -> bytes:
        """Get compressed public key (33 bytes)."""
        if self._public_key_compressed is None:
            self._public_key_compressed = self.curve.compress_point(self.public_key)
        return self._public_key_compressed
    
    @property
    def public_key_uncompressed(self) -> bytes:
        """Get uncompressed public key (65 bytes)."""
        if self._public_key_uncompressed is None:
            if self.public_key.is_infinity:
                self._public_key_uncompressed = b'\x00'
            else:
                prefix = b'\x04'
                x_bytes = self.public_key.x.to_bytes(32, 'big')
                y_bytes = self.public_key.y.to_bytes(32, 'big')
                self._public_key_uncompressed = prefix + x_bytes + y_bytes
        return self._public_key_uncompressed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert key pair to dictionary representation."""
        return {
            "private_key_hex": format(self.private_key, '064x'),
            "public_key_compressed": self.public_key_compressed.hex(),
            "public_key_uncompressed": self.public_key_uncompressed.hex(),
            "public_key_x": hex(self.public_key.x) if not self.public_key.is_infinity else None,
            "public_key_y": hex(self.public_key.y) if not self.public_key.is_infinity else None
        }
    
    def validate(self) -> AuthenticationResult:
        """Validate the key pair."""
        errors = []
        warnings = []
        
        # Check private key range
        if not (1 <= self.private_key < self.curve.n):
            errors.append("Private key out of valid range")
        
        # Check public key is on curve
        if not self.curve.is_on_curve(self.public_key):
            errors.append("Public key not on curve")
        
        # Check for weak keys
        if self.private_key < 1000:
            warnings.append("Very small private key (weak)")
        
        if self.private_key > self.curve.n - 1000:
            warnings.append("Private key very close to curve order (weak)")
        
        return AuthenticationResult(
            success=len(errors) == 0,
            data=self.to_dict(),
            error="; ".join(errors) if errors else None,
            warnings=warnings
        )
