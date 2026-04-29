"""
Authentication Interface for 256-bit ECC Private Key Access

Provides a clean, modular interface for accessing and validating
256-bit private keys via ECC cryptography operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging


@dataclass
class AuthenticationResult:
    """Standard result format for authentication operations."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class PrivateKeyCredentials:
    """Standard format for private key credentials."""
    hex_key: str
    wif_key: Optional[str] = None
    is_compressed: bool = True
    network: str = "mainnet"
    key_int: Optional[int] = None


class AuthenticationInterface(ABC):
    """
    Abstract interface for ECC authentication operations.
    
    Defines the contract for all authentication implementations,
    ensuring consistent behavior across different cryptographic backends.
    """
    
    @abstractmethod
    def validate_private_key(self, key_data: str, key_format: str = "hex") -> AuthenticationResult:
        """
        Validate a private key in specified format.
        
        Args:
            key_data: The key data (hex, WIF, etc.)
            key_format: Format of the key ("hex", "wif", "bytes")
            
        Returns:
            AuthenticationResult with validation details
        """
        pass
    
    @abstractmethod
    def generate_private_key(self, compressed: bool = True, network: str = "mainnet") -> AuthenticationResult:
        """
        Generate a new cryptographically secure private key.
        
        Args:
            compressed: Whether to use compressed format
            network: Network type ("mainnet", "testnet")
            
        Returns:
            AuthenticationResult with generated key
        """
        pass
    
    @abstractmethod
    def convert_key_format(self, key_data: str, from_format: str, to_format: str) -> AuthenticationResult:
        """
        Convert private key between formats.
        
        Args:
            key_data: The key data to convert
            from_format: Source format ("hex", "wif")
            to_format: Target format ("hex", "wif")
            
        Returns:
            AuthenticationResult with converted key
        """
        pass
    
    @abstractmethod
    def get_public_key(self, private_key: str, compressed: bool = True) -> AuthenticationResult:
        """
        Derive public key from private key.
        
        Args:
            private_key: Private key in hex format
            compressed: Whether to return compressed public key
            
        Returns:
            AuthenticationResult with public key
        """
        pass
    
    @abstractmethod
    def sign_message(self, private_key: str, message: str) -> AuthenticationResult:
        """
        Sign a message with private key.
        
        Args:
            private_key: Private key in hex format
            message: Message to sign
            
        Returns:
            AuthenticationResult with signature
        """
        pass
    
    @abstractmethod
    def verify_signature(self, public_key: str, message: str, signature: str) -> AuthenticationResult:
        """
        Verify a message signature.
        
        Args:
            public_key: Public key in hex format
            message: Original message
            signature: Signature to verify
            
        Returns:
            AuthenticationResult with verification result
        """
        pass


class AuthenticationConfig:
    """Configuration management for authentication operations."""
    
    def __init__(self):
        self.secp256k1_params = {
            'p': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,
            'a': 0,
            'b': 7,
            'gx': 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
            'gy': 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
            'n': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        }
        
        self.wif_params = {
            'mainnet_version': 0x80,
            'testnet_version': 0xEF,
            'compressed_suffix': 0x01
        }
        
        self.validation_params = {
            'allow_testnet': True,
            'strict_checksum': True,
            'check_low_entropy': True
        }
        
        self.security_params = {
            'min_entropy_bits': 128,
            'warn_repeated_bytes': True,
            'max_validation_attempts': 3
        }
    
    def update_config(self, section: str, updates: Dict[str, Any]) -> None:
        """Update configuration parameters."""
        if hasattr(self, f"{section}_params"):
            current = getattr(self, f"{section}_params")
            current.update(updates)
        else:
            raise ValueError(f"Unknown configuration section: {section}")
    
    def get_config(self, section: str) -> Dict[str, Any]:
        """Get configuration parameters for a section."""
        if hasattr(self, f"{section}_params"):
            return getattr(self, f"{section}_params")
        else:
            raise ValueError(f"Unknown configuration section: {section}")


class AuthenticationLogger:
    """Centralized logging for authentication operations."""
    
    def __init__(self, name: str = "authentication"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_validation_attempt(self, key_format: str, key_preview: str):
        """Log a key validation attempt."""
        self.logger.info(f"Validating {key_format} key: {key_preview}...")
    
    def log_generation_attempt(self, compressed: bool, network: str):
        """Log a key generation attempt."""
        self.logger.info(f"Generating {'compressed' if compressed else 'uncompressed'} key for {network}")
    
    def log_conversion_attempt(self, from_format: str, to_format: str):
        """Log a format conversion attempt."""
        self.logger.info(f"Converting key from {from_format} to {to_format}")
    
    def log_security_warning(self, warning: str):
        """Log a security warning."""
        self.logger.warning(f"SECURITY WARNING: {warning}")
    
    def log_error(self, operation: str, error: str):
        """Log an operation error."""
        self.logger.error(f"Error in {operation}: {error}")
    
    def log_success(self, operation: str, details: str = ""):
        """Log a successful operation."""
        if details:
            self.logger.info(f"Success: {operation} - {details}")
        else:
            self.logger.info(f"Success: {operation}")
    
    def log_info(self, message: str):
        """Log an informational message."""
        self.logger.info(message)
