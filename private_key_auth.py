"""
Refactored Private Key Authentication Module

Provides clean, modular private key validation and format conversion
with improved error handling and separation of concerns.
"""

import os
import hashlib
from typing import Dict, Any, Optional
import logging

from authentication_interface import (
    AuthenticationInterface, AuthenticationResult, 
    PrivateKeyCredentials, AuthenticationConfig, AuthenticationLogger
)
from ecc_operations import Secp256k1Curve, ECCKeyPair

try:
    from vortex_cluster_api import VortexClusterAPI
except ImportError:
    VortexClusterAPI = None


class Base58Validator:
    """Handles Base58 encoding/decoding operations."""
    
    ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    
    @classmethod
    def encode(cls, data: bytes) -> str:
        """Encode bytes to Base58 string."""
        num = int.from_bytes(data, 'big')
        result = ""
        
        while num > 0:
            num, remainder = divmod(num, 58)
            result = cls.ALPHABET[remainder] + result
        
        # Add leading '1's for leading zero bytes
        for byte in data:
            if byte == 0:
                result = "1" + result
            else:
                break
        
        return result or '1'
    
    @classmethod
    def decode(cls, s: str) -> bytes:
        """Decode Base58 string to bytes."""
        num = 0
        
        for char in s:
            if char not in cls.ALPHABET:
                raise ValueError(f"Invalid Base58 character: {char}")
            num = num * 58 + cls.ALPHABET.index(char)
        
        # Convert to bytes
        result = []
        temp = num
        while temp > 0:
            temp, remainder = divmod(temp, 256)
            result.insert(0, remainder)
        
        # Add leading zeros for leading '1's
        leading_ones = 0
        for char in s:
            if char == '1':
                leading_ones += 1
            else:
                break
        
        result = [0] * leading_ones + result
        return bytes(result)


class PrivateKeyValidator(AuthenticationInterface):
    """
    Refactored private key validator implementing the AuthenticationInterface.
    
    Provides clean validation and conversion between different key formats
    with improved modularity and error handling.
    """
    
    def __init__(self, config: AuthenticationConfig = None):
        self.config = config or AuthenticationConfig()
        self.logger = AuthenticationLogger("private_key_validator")
        self.curve = Secp256k1Curve(self.config)
        self.base58 = Base58Validator()
        
        # Load configuration
        self.wif_params = self.config.get_config("wif")
        self.validation_params = self.config.get_config("validation")
        self.security_params = self.config.get_config("security")
        
        # Cluster halt awareness
        if VortexClusterAPI:
            try:
                self.cluster_api = VortexClusterAPI()
            except Exception:
                self.cluster_api = None
        else:
            self.cluster_api = None
        
        self.logger.log_success("Private key validator initialized")
    
    def validate_private_key(self, key_data: str, key_format: str = "hex") -> AuthenticationResult:
        """Validate a private key in specified format."""
        self.logger.log_validation_attempt(key_format, key_data[:10] + "...")
        
        try:
            if key_format.lower() == "hex":
                return self._validate_hex_key(key_data)
            elif key_format.lower() == "wif":
                return self._validate_wif_key(key_data)
            else:
                return AuthenticationResult(
                    success=False,
                    error=f"Unsupported key format: {key_format}"
                )
        except Exception as e:
            self.logger.log_error("key validation", str(e))
            return AuthenticationResult(
                success=False,
                error=f"Validation failed: {str(e)}"
            )
    
    def _validate_hex_key(self, hex_key: str) -> AuthenticationResult:
        """Validate a hex-encoded private key."""
        warnings = []
        
        # Clean the key
        hex_clean = hex_key.strip().lower()
        if hex_clean.startswith('0x'):
            hex_clean = hex_clean[2:]
        
        # Check length
        if len(hex_clean) not in [64, 66]:
            return AuthenticationResult(
                success=False,
                error=f"Invalid length: {len(hex_clean)} chars (expected 64 or 66)"
            )
        
        # Check valid hex
        try:
            key_bytes = bytes.fromhex(hex_clean)
        except ValueError:
            return AuthenticationResult(
                success=False,
                error="Invalid hex characters"
            )
        
        # Check compressed flag
        is_compressed = False
        if len(key_bytes) == 33:
            suffix = key_bytes[-1]
            if suffix == 0x01:
                key_bytes = key_bytes[:-1]
                is_compressed = True
            else:
                return AuthenticationResult(
                    success=False,
                    error=f"Invalid compression byte: {hex(suffix)}"
                )
        
        # Convert to integer and check range
        key_int = int.from_bytes(key_bytes, 'big')
        
        if key_int == 0:
            return AuthenticationResult(
                success=False,
                error="Key is zero (INVALID)"
            )
        elif key_int >= self.curve.n:
            return AuthenticationResult(
                success=False,
                error=f"Key >= curve order (INVALID)"
            )
        elif key_int < 1:
            return AuthenticationResult(
                success=False,
                error="Key must be >= 1"
            )
        
        # Security checks
        if self.security_params.get('check_low_entropy', True):
            if key_bytes in [b'\x00' * 31 + b'\x01', b'\x01' + b'\x00' * 31]:
                warnings.append("Very low entropy key detected")
                self.logger.log_security_warning("Very low entropy key detected")
            
            if len(set(key_bytes)) < 4:
                warnings.append("Low entropy: too many repeated bytes")
                self.logger.log_security_warning("Low entropy key with repeated bytes")
        
        # Create key pair for full validation
        key_pair = ECCKeyPair(key_int, self.curve)
        key_pair_validation = key_pair.validate()
        
        if not key_pair_validation.success:
            return key_pair_validation
        
        warnings.extend(key_pair_validation.warnings)
        
        return AuthenticationResult(
            success=True,
            data={
                "hex_key": hex_clean,
                "key_bytes": key_bytes.hex(),
                "key_int": key_int,
                "is_compressed": is_compressed,
                "key_pair": key_pair.to_dict()
            },
            warnings=warnings
        )
    
    def _validate_wif_key(self, wif_key: str) -> AuthenticationResult:
        """Validate a WIF-encoded private key."""
        warnings = []
        
        # Check WIF format
        if not (50 <= len(wif_key) <= 52):
            return AuthenticationResult(
                success=False,
                error=f"Invalid WIF length: {len(wif_key)} chars (expected 50-52)"
            )
        
        # Check prefix and determine properties
        prefix = wif_key[0]
        if prefix == '5':
            is_compressed = False
            network = "mainnet"
            version_byte = self.wif_params['mainnet_version']
        elif prefix in ['K', 'L']:
            is_compressed = True
            network = "mainnet"
            version_byte = self.wif_params['mainnet_version']
        else:
            return AuthenticationResult(
                success=False,
                error=f"Invalid WIF prefix: '{prefix}' (expected '5', 'K', or 'L')"
            )
        
        # Decode Base58
        try:
            decoded = self.base58.decode(wif_key)
        except Exception as e:
            return AuthenticationResult(
                success=False,
                error=f"Base58 decode failed: {e}"
            )
        
        # Check decoded length
        expected_len = 38 if is_compressed else 37
        if len(decoded) < expected_len - 1 or len(decoded) > expected_len:
            return AuthenticationResult(
                success=False,
                error=f"Decoded length: {len(decoded)} bytes (expected {expected_len-1}-{expected_len})"
            )
        
        # Pad with leading zeros if shorter
        if len(decoded) < expected_len:
            decoded = bytes(expected_len - len(decoded)) + decoded
        
        # Verify version byte
        if decoded[0] != version_byte:
            return AuthenticationResult(
                success=False,
                error=f"Wrong version byte: {decoded[0]} (expected {version_byte})"
            )
        
        # Extract components
        if is_compressed:
            key_bytes = decoded[1:33]
            compress_byte = decoded[33]
            checksum_stored = decoded[34:38]
            payload = decoded[:34]
            
            if compress_byte != self.wif_params['compressed_suffix']:
                return AuthenticationResult(
                    success=False,
                    error=f"Invalid compression byte: {hex(compress_byte)}"
                )
        else:
            key_bytes = decoded[1:33]
            checksum_stored = decoded[33:37]
            payload = decoded[:33]
        
        # Verify checksum
        checksum_computed = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        if self.validation_params.get('strict_checksum', True):
            if checksum_stored != checksum_computed:
                return AuthenticationResult(
                    success=False,
                    error="Invalid checksum (possible corrupted key)"
                )
        
        # Validate key range
        key_int = int.from_bytes(key_bytes, 'big')
        
        if key_int == 0:
            return AuthenticationResult(
                success=False,
                error="Key is zero (INVALID)"
            )
        elif key_int >= self.curve.n:
            return AuthenticationResult(
                success=False,
                error="Key >= curve order (INVALID)"
            )
        
        # Create hex representation
        hex_key = key_bytes.hex()
        if is_compressed:
            hex_key += "01"
        
        return AuthenticationResult(
            success=True,
            data={
                "hex_key": hex_key,
                "wif_key": wif_key,
                "key_bytes": key_bytes.hex(),
                "key_int": key_int,
                "is_compressed": is_compressed,
                "network": network,
                "checksum_valid": checksum_stored == checksum_computed
            },
            warnings=warnings
        )
    
    def generate_private_key(self, compressed: bool = True, network: str = "mainnet") -> AuthenticationResult:
        """Generate a new cryptographically secure private key."""
        self.logger.log_generation_attempt(compressed, network)
        
        # Respect global cluster halt signal
        if self.cluster_api and self.cluster_api.check_global_halt():
            return AuthenticationResult(success=False, error="Cluster: global halt received")
        
        max_attempts = self.security_params.get('max_validation_attempts', 3)
        
        for attempt in range(max_attempts):
            try:
                # Generate random bytes
                key_bytes = os.urandom(32)
                key_int = int.from_bytes(key_bytes, 'big')
                
                # Check if key is in valid range
                if 1 <= key_int < self.curve.n:
                    # Create key pair for validation
                    key_pair = ECCKeyPair(key_int, self.curve)
                    validation = key_pair.validate()
                    
                    if validation.success:
                        # Convert to requested format
                        hex_key = format(key_int, '064x')
                        if compressed:
                            hex_key += "01"
                        
                        # Generate WIF if needed
                        wif_key = self._hex_to_wif(hex_key, compressed, network)
                        
                        self.logger.log_success("key generation", f"Generated {network} {'compressed' if compressed else 'uncompressed'} key")
                        
                        return AuthenticationResult(
                            success=True,
                            data={
                                "hex_key": hex_key,
                                "wif_key": wif_key,
                                "key_bytes": key_bytes.hex(),
                                "key_int": key_int,
                                "is_compressed": compressed,
                                "network": network,
                                "key_pair": key_pair.to_dict()
                            }
                        )
                        break
                    else:
                        self.logger.log_security_warning(f"Generated weak key on attempt {attempt + 1}: {validation.warnings}")
                        
            except Exception as e:
                self.logger.log_error("key generation", f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    return AuthenticationResult(
                        success=False,
                        error=f"Failed to generate valid key after {max_attempts} attempts"
                    )
        
        return AuthenticationResult(
            success=False,
            error=f"Failed to generate valid key after {max_attempts} attempts"
        )
    
    def convert_key_format(self, key_data: str, from_format: str, to_format: str) -> AuthenticationResult:
        """Convert private key between formats."""
        self.logger.log_conversion_attempt(from_format, to_format)
        
        # First validate the key in source format
        validation = self.validate_private_key(key_data, from_format)
        if not validation.success:
            return validation
        
        key_int = validation.data["key_int"]
        is_compressed = validation.data.get("is_compressed", True)
        network = validation.data.get("network", "mainnet")
        
        if to_format.lower() == "hex":
            hex_key = format(key_int, '064x')
            if is_compressed:
                hex_key += "01"
            
            return AuthenticationResult(
                success=True,
                data={
                    "hex_key": hex_key,
                    "key_int": key_int,
                    "is_compressed": is_compressed
                }
            )
        
        elif to_format.lower() == "wif":
            hex_key = format(key_int, '064x')
            wif_key = self._hex_to_wif(hex_key, is_compressed, network)
            
            return AuthenticationResult(
                success=True,
                data={
                    "wif_key": wif_key,
                    "key_int": key_int,
                    "is_compressed": is_compressed,
                    "network": network
                }
            )
        
        else:
            return AuthenticationResult(
                success=False,
                error=f"Unsupported target format: {to_format}"
            )
    
    def _hex_to_wif(self, hex_key: str, compressed: bool, network: str) -> str:
        """Convert hex key to WIF format."""
        # Get version byte
        version = self.wif_params['mainnet_version'] if network == "mainnet" else self.wif_params['testnet_version']
        
        # Build payload
        key_bytes = bytes.fromhex(hex_key.lower().replace('0x', ''))
        if len(key_bytes) == 33 and key_bytes[-1] == 0x01:
            key_bytes = key_bytes[:-1]
        
        payload = bytes([version]) + key_bytes
        if compressed:
            payload += bytes([self.wif_params['compressed_suffix']])
        
        # Add checksum
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        final = payload + checksum
        
        return self.base58.encode(final)
    
    def get_public_key(self, private_key: str, compressed: bool = True) -> AuthenticationResult:
        """Derive public key from private key."""
        validation = self.validate_private_key(private_key, "hex")
        if not validation.success:
            return validation
        
        key_int = validation.data["key_int"]
        key_pair = ECCKeyPair(key_int, self.curve)
        
        if compressed:
            pub_key = key_pair.public_key_compressed.hex()
        else:
            pub_key = key_pair.public_key_uncompressed.hex()
        
        return AuthenticationResult(
            success=True,
            data={
                "public_key": pub_key,
                "compressed": compressed,
                "public_key_x": hex(key_pair.public_key.x) if not key_pair.public_key.is_infinity else None,
                "public_key_y": hex(key_pair.public_key.y) if not key_pair.public_key.is_infinity else None
            }
        )
    
    def sign_message(self, private_key: str, message: str) -> AuthenticationResult:
        """Sign a message with private key."""
        # This would implement ECDSA signing
        # For now, return a placeholder
        return AuthenticationResult(
            success=False,
            error="Message signing not implemented in this version"
        )
    
    def verify_signature(self, public_key: str, message: str, signature: str) -> AuthenticationResult:
        """Verify a message signature."""
        # This would implement ECDSA verification
        # For now, return a placeholder
        return AuthenticationResult(
            success=False,
            error="Signature verification not implemented in this version"
        )
