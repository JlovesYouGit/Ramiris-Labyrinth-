"""
Refactored Authentication Orchestrator

Main orchestrator for ECC authentication operations using dependency injection.
Provides a clean interface for accessing 256-bit private keys via ECC cryptography.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from authentication_interface import (
    AuthenticationInterface, AuthenticationResult, 
    AuthenticationConfig, AuthenticationLogger
)
from private_key_auth import PrivateKeyValidator
from ecc_operations import Secp256k1Curve, ECCKeyPair


@dataclass
class AuthenticationRequest:
    """Standard format for authentication requests."""
    operation: str
    parameters: Dict[str, Any]
    request_id: Optional[str] = None


@dataclass
class AuthenticationResponse:
    """Standard format for authentication responses."""
    request_id: Optional[str]
    operation: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    warnings: List[str] = None
    execution_time_ms: Optional[float] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class AuthenticationOrchestrator:
    """
    Main authentication orchestrator using dependency injection pattern.
    
    Coordinates various authentication components and provides a unified
    interface for ECC cryptographic operations.
    """
    
    def __init__(self, 
                 auth_interface: AuthenticationInterface = None,
                 config: AuthenticationConfig = None,
                 logger: AuthenticationLogger = None):
        """
        Initialize orchestrator with dependency injection.
        
        Args:
            auth_interface: Authentication implementation (defaults to PrivateKeyValidator)
            config: Configuration object
            logger: Logger instance
        """
        self.config = config or AuthenticationConfig()
        self.logger = logger or AuthenticationLogger("orchestrator")
        
        # Inject dependencies
        self.auth_interface = auth_interface or PrivateKeyValidator(self.config)
        self.curve = Secp256k1Curve(self.config)
        
        # Operation registry for extensibility
        self.operations = {
            'validate_key': self._validate_key,
            'generate_key': self._generate_key,
            'convert_format': self._convert_format,
            'get_public_key': self._get_public_key,
            'create_key_pair': self._create_key_pair,
            'batch_validate': self._batch_validate,
            'security_audit': self._security_audit
        }
        
        self.logger.log_success("Authentication orchestrator initialized", f"with {len(self.operations)} operations")
    
    def execute(self, request: AuthenticationRequest) -> AuthenticationResponse:
        """
        Execute an authentication request.
        
        Args:
            request: Authentication request with operation and parameters
            
        Returns:
            Authentication response with results
        """
        import time
        start_time = time.time()
        
        self.logger.log_info(f"Executing operation: {request.operation}")
        
        try:
            if request.operation not in self.operations:
                return AuthenticationResponse(
                    request_id=request.request_id,
                    operation=request.operation,
                    success=False,
                    error=f"Unknown operation: {request.operation}"
                )
            
            # Execute the operation
            result = self.operations[request.operation](request.parameters)
            
            execution_time = (time.time() - start_time) * 1000
            
            if isinstance(result, AuthenticationResult):
                return AuthenticationResponse(
                    request_id=request.request_id,
                    operation=request.operation,
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    warnings=result.warnings,
                    execution_time_ms=execution_time
                )
            else:
                return AuthenticationResponse(
                    request_id=request.request_id,
                    operation=request.operation,
                    success=True,
                    data=result,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_error(request.operation, str(e))
            
            return AuthenticationResponse(
                request_id=request.request_id,
                operation=request.operation,
                success=False,
                error=f"Operation failed: {str(e)}",
                execution_time_ms=execution_time
            )
    
    def _validate_key(self, params: Dict[str, Any]) -> AuthenticationResult:
        """Validate a private key."""
        key_data = params.get('key_data')
        key_format = params.get('key_format', 'hex')
        
        if not key_data:
            return AuthenticationResult(
                success=False,
                error="Missing required parameter: key_data"
            )
        
        return self.auth_interface.validate_private_key(key_data, key_format)
    
    def _generate_key(self, params: Dict[str, Any]) -> AuthenticationResult:
        """Generate a new private key."""
        compressed = params.get('compressed', True)
        network = params.get('network', 'mainnet')
        
        return self.auth_interface.generate_private_key(compressed, network)
    
    def _convert_format(self, params: Dict[str, Any]) -> AuthenticationResult:
        """Convert key between formats."""
        key_data = params.get('key_data')
        from_format = params.get('from_format')
        to_format = params.get('to_format')
        
        if not all([key_data, from_format, to_format]):
            return AuthenticationResult(
                success=False,
                error="Missing required parameters: key_data, from_format, to_format"
            )
        
        return self.auth_interface.convert_key_format(key_data, from_format, to_format)
    
    def _get_public_key(self, params: Dict[str, Any]) -> AuthenticationResult:
        """Get public key from private key."""
        private_key = params.get('private_key')
        compressed = params.get('compressed', True)
        
        if not private_key:
            return AuthenticationResult(
                success=False,
                error="Missing required parameter: private_key"
            )
        
        return self.auth_interface.get_public_key(private_key, compressed)
    
    def _create_key_pair(self, params: Dict[str, Any]) -> AuthenticationResult:
        """Create a complete key pair with validation."""
        # Generate key first
        gen_result = self._generate_key(params)
        if not gen_result.success:
            return gen_result
        
        # Get public key
        private_key = gen_result.data['hex_key']
        pub_result = self._get_public_key({
            'private_key': private_key,
            'compressed': gen_result.data.get('is_compressed', True)
        })
        
        if not pub_result.success:
            return pub_result
        
        # Combine results
        combined_data = gen_result.data.copy()
        combined_data.update(pub_result.data)
        
        return AuthenticationResult(
            success=True,
            data=combined_data,
            warnings=gen_result.warnings + pub_result.warnings
        )
    
    def _batch_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate multiple keys in batch."""
        keys = params.get('keys', [])
        key_format = params.get('key_format', 'hex')
        
        results = []
        success_count = 0
        
        for i, key_data in enumerate(keys):
            result = self._validate_key({
                'key_data': key_data,
                'key_format': key_format
            })
            
            results.append({
                'index': i,
                'key_preview': key_data[:10] + "..." if len(key_data) > 10 else key_data,
                'result': result.__dict__
            })
            
            if result.success:
                success_count += 1
        
        return {
            'total_keys': len(keys),
            'valid_keys': success_count,
            'invalid_keys': len(keys) - success_count,
            'results': results
        }
    
    def _security_audit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform security audit on keys or configuration."""
        audit_type = params.get('type', 'configuration')
        
        if audit_type == 'configuration':
            return self._audit_configuration()
        elif audit_type == 'key':
            key_data = params.get('key_data')
            key_format = params.get('key_format', 'hex')
            return self._audit_key(key_data, key_format)
        else:
            return {'error': f'Unknown audit type: {audit_type}'}
    
    def _audit_configuration(self) -> Dict[str, Any]:
        """Audit current configuration for security issues."""
        findings = []
        
        # Check curve parameters
        curve_info = self.curve.get_curve_info()
        findings.append({
            'category': 'curve_security',
            'status': 'info',
            'message': f"Using {curve_info['curve_name']} with {curve_info['security_bits']} bits of security"
        })
        
        # Check validation parameters
        validation_params = self.config.get_config("validation")
        if not validation_params.get('strict_checksum', True):
            findings.append({
                'category': 'validation',
                'status': 'warning',
                'message': 'Strict checksum validation is disabled'
            })
        
        # Check security parameters
        security_params = self.config.get_config("security")
        min_entropy = security_params.get('min_entropy_bits', 128)
        if min_entropy < 128:
            findings.append({
                'category': 'entropy',
                'status': 'warning',
                'message': f'Low minimum entropy threshold: {min_entropy} bits'
            })
        
        return {
            'audit_type': 'configuration',
            'findings': findings,
            'overall_status': 'secure' if all(f['status'] != 'warning' for f in findings) else 'warning'
        }
    
    def _audit_key(self, key_data: str, key_format: str) -> Dict[str, Any]:
        """Audit a specific key for security issues."""
        validation = self._validate_key({'key_data': key_data, 'key_format': key_format})
        
        findings = []
        
        if not validation.success:
            findings.append({
                'category': 'validity',
                'status': 'error',
                'message': validation.error
            })
        else:
            findings.append({
                'category': 'validity',
                'status': 'info',
                'message': 'Key is valid and in correct range'
            })
            
            # Check for warnings
            for warning in validation.warnings:
                findings.append({
                    'category': 'security',
                    'status': 'warning',
                    'message': warning
                })
        
        return {
            'audit_type': 'key',
            'key_preview': key_data[:10] + "..." if len(key_data) > 10 else key_data,
            'findings': findings,
            'overall_status': 'secure' if all(f['status'] != 'warning' and f['status'] != 'error' for f in findings) else 'warning' if any(f['status'] == 'warning' for f in findings) else 'error'
        }
    
    def get_available_operations(self) -> List[str]:
        """Get list of available operations."""
        return list(self.operations.keys())
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and status."""
        return {
            'orchestrator_version': '2.0.0',
            'auth_interface': type(self.auth_interface).__name__,
            'curve_info': self.curve.get_curve_info(),
            'available_operations': self.get_available_operations(),
            'config_sections': ['secp256k1', 'wif', 'validation', 'security']
        }


class AuthenticationClient:
    """
    High-level client for authentication operations.
    
    Provides a simplified interface for common authentication tasks.
    """
    
    def __init__(self, orchestrator: AuthenticationOrchestrator = None):
        self.orchestrator = orchestrator or AuthenticationOrchestrator()
        self.logger = AuthenticationLogger("client")
    
    def validate_key(self, key_data: str, key_format: str = "hex") -> AuthenticationResponse:
        """Validate a private key."""
        request = AuthenticationRequest(
            operation='validate_key',
            parameters={'key_data': key_data, 'key_format': key_format}
        )
        return self.orchestrator.execute(request)
    
    def generate_key(self, compressed: bool = True, network: str = "mainnet") -> AuthenticationResponse:
        """Generate a new private key."""
        request = AuthenticationRequest(
            operation='generate_key',
            parameters={'compressed': compressed, 'network': network}
        )
        return self.orchestrator.execute(request)
    
    def create_key_pair(self, compressed: bool = True, network: str = "mainnet") -> AuthenticationResponse:
        """Create a complete key pair."""
        request = AuthenticationRequest(
            operation='create_key_pair',
            parameters={'compressed': compressed, 'network': network}
        )
        return self.orchestrator.execute(request)
    
    def convert_to_wif(self, hex_key: str) -> AuthenticationResponse:
        """Convert hex key to WIF format."""
        request = AuthenticationRequest(
            operation='convert_format',
            parameters={
                'key_data': hex_key,
                'from_format': 'hex',
                'to_format': 'wif'
            }
        )
        return self.orchestrator.execute(request)
    
    def convert_to_hex(self, wif_key: str) -> AuthenticationResponse:
        """Convert WIF key to hex format."""
        request = AuthenticationRequest(
            operation='convert_format',
            parameters={
                'key_data': wif_key,
                'from_format': 'wif',
                'to_format': 'hex'
            }
        )
        return self.orchestrator.execute(request)
    
    def get_public_key(self, private_key: str, compressed: bool = True) -> AuthenticationResponse:
        """Get public key from private key."""
        request = AuthenticationRequest(
            operation='get_public_key',
            parameters={'private_key': private_key, 'compressed': compressed}
        )
        return self.orchestrator.execute(request)
    
    def batch_validate(self, keys: List[str], key_format: str = "hex") -> AuthenticationResponse:
        """Validate multiple keys."""
        request = AuthenticationRequest(
            operation='batch_validate',
            parameters={'keys': keys, 'key_format': key_format}
        )
        return self.orchestrator.execute(request)
    
    def security_audit(self, audit_type: str = "configuration", key_data: str = None) -> AuthenticationResponse:
        """Perform security audit."""
        params = {'type': audit_type}
        if key_data:
            params['key_data'] = key_data
        
        request = AuthenticationRequest(
            operation='security_audit',
            parameters=params
        )
        return self.orchestrator.execute(request)
