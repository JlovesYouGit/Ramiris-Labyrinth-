"""
Demonstration of Refactored Authentication Module

Shows how to use the new modular authentication system for
accessing 256-bit private keys via ECC cryptography.
"""

import os
from dotenv import load_dotenv

from authentication_orchestrator import AuthenticationClient, AuthenticationOrchestrator
from authentication_interface import AuthenticationConfig
from private_key_auth import PrivateKeyValidator


def main():
    """Demonstrate the refactored authentication module."""
    
    print("=" * 70)
    print("   REFACTORED ECC AUTHENTICATION DEMONSTRATION")
    print("=" * 70)
    
    # Load environment variables
    load_dotenv()
    cred_name = os.getenv("CRED_NAME", "demo")
    target_address = os.getenv("CRED_SHA1", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    
    print(f"\n[*] Credential: {cred_name}")
    print(f"[*] Target Address: {target_address}")
    
    # Initialize the authentication client
    print("\n[+] Initializing Authentication Client...")
    client = AuthenticationClient()
    
    # Get system information
    print("\n[PHASE 1] System Information")
    print("-" * 40)
    system_info = client.orchestrator.get_system_info()
    print(f"    Orchestrator Version: {system_info['orchestrator_version']}")
    print(f"    Auth Interface: {system_info['auth_interface']}")
    print(f"    Curve: {system_info['curve_info']['curve_name']}")
    print(f"    Security Bits: {system_info['curve_info']['security_bits']}")
    print(f"    Available Operations: {len(system_info['available_operations'])}")
    
    # Generate a new key pair
    print("\n[PHASE 2] Key Generation")
    print("-" * 40)
    print("[*] Generating new 256-bit private key...")
    key_result = client.create_key_pair(compressed=True, network="mainnet")
    
    if key_result.success:
        key_data = key_result.data
        print(f"    ✓ Private Key (hex): {key_data['hex_key'][:20]}...{key_data['hex_key'][-8:]}")
        print(f"    ✓ Private Key (WIF): {key_data['wif_key'][:20]}...{key_data['wif_key'][-8:]}")
        print(f"    ✓ Public Key (compressed): {key_data['public_key'][:30]}...")
        print(f"    ✓ Network: {key_data['network']}")
        print(f"    ✓ Compressed: {key_data['is_compressed']}")
        print(f"    ✓ Execution Time: {key_result.execution_time_ms:.2f}ms")
        
        if key_result.warnings:
            for warning in key_result.warnings:
                print(f"    ⚠ Warning: {warning}")
    else:
        print(f"    ✗ Key generation failed: {key_result.error}")
        return
    
    # Validate the generated key
    print("\n[PHASE 3] Key Validation")
    print("-" * 40)
    print("[*] Validating generated key in hex format...")
    hex_validation = client.validate_key(key_data['hex_key'], 'hex')
    
    if hex_validation.success:
        print(f"    ✓ Hex key is valid")
        print(f"    ✓ Key integer: {hex_validation.data['key_int']}")
        print(f"    ✓ Compressed: {hex_validation.data['is_compressed']}")
    else:
        print(f"    ✗ Hex validation failed: {hex_validation.error}")
    
    print("[*] Validating generated key in WIF format...")
    wif_validation = client.validate_key(key_data['wif_key'], 'wif')
    
    if wif_validation.success:
        print(f"    ✓ WIF key is valid")
        print(f"    ✓ Checksum valid: {wif_validation.data['checksum_valid']}")
        print(f"    ✓ Network: {wif_validation.data['network']}")
    else:
        print(f"    ✗ WIF validation failed: {wif_validation.error}")
    
    # Format conversion
    print("\n[PHASE 4] Format Conversion")
    print("-" * 40)
    print("[*] Converting hex to WIF...")
    hex_to_wif = client.convert_to_wif(key_data['hex_key'])
    
    if hex_to_wif.success:
        print(f"    ✓ Conversion successful")
        print(f"    ✓ WIF matches original: {hex_to_wif.data['wif_key'] == key_data['wif_key']}")
    else:
        print(f"    ✗ Conversion failed: {hex_to_wif.error}")
    
    print("[*] Converting WIF to hex...")
    wif_to_hex = client.convert_to_hex(key_data['wif_key'])
    
    if wif_to_hex.success:
        print(f"    ✓ Conversion successful")
        print(f"    ✓ Hex matches original: {wif_to_hex.data['hex_key'] == key_data['hex_key']}")
    else:
        print(f"    ✗ Conversion failed: {wif_to_hex.error}")
    
    # Public key derivation
    print("\n[PHASE 5] Public Key Operations")
    print("-" * 40)
    print("[*] Getting compressed public key...")
    pub_compressed = client.get_public_key(key_data['hex_key'], compressed=True)
    
    if pub_compressed.success:
        print(f"    ✓ Compressed public key: {pub_compressed.data['public_key'][:30]}...")
        print(f"    ✓ X coordinate: {pub_compressed.data['public_key_x'][:20]}...")
        print(f"    ✓ Y coordinate: {pub_compressed.data['public_key_y'][:20]}...")
    else:
        print(f"    ✗ Failed to get compressed public key: {pub_compressed.error}")
    
    print("[*] Getting uncompressed public key...")
    pub_uncompressed = client.get_public_key(key_data['hex_key'], compressed=False)
    
    if pub_uncompressed.success:
        print(f"    ✓ Uncompressed public key: {pub_uncompressed.data['public_key'][:30]}...")
    else:
        print(f"    ✗ Failed to get uncompressed public key: {pub_uncompressed.error}")
    
    # Batch validation
    print("\n[PHASE 6] Batch Operations")
    print("-" * 40)
    test_keys = [
        key_data['hex_key'],
        "0" * 64,  # Invalid zero key
        "F" * 64,  # Invalid key (too large)
        key_data['wif_key']
    ]
    
    print(f"[*] Validating {len(test_keys)} keys in batch...")
    batch_result = client.batch_validate(test_keys, 'hex')
    
    if batch_result.success:
        batch_data = batch_result.data
        print(f"    ✓ Total keys: {batch_data['total_keys']}")
        print(f"    ✓ Valid keys: {batch_data['valid_keys']}")
        print(f"    ✓ Invalid keys: {batch_data['invalid_keys']}")
        print(f"    ✓ Execution time: {batch_result.execution_time_ms:.2f}ms")
        
        # Show individual results
        for result in batch_data['results'][:2]:  # Show first 2
            status = "✓" if result['result']['success'] else "✗"
            print(f"    {status} {result['key_preview']}: {result['result']['error'] if not result['result']['success'] else 'Valid'}")
    else:
        print(f"    ✗ Batch validation failed: {batch_result.error}")
    
    # Security audit
    print("\n[PHASE 7] Security Audit")
    print("-" * 40)
    print("[*] Performing configuration security audit...")
    config_audit = client.security_audit('configuration')
    
    if config_audit.success:
        audit_data = config_audit.data
        print(f"    ✓ Overall status: {audit_data['overall_status']}")
        for finding in audit_data['findings']:
            status_icon = "✓" if finding['status'] == 'info' else "⚠" if finding['status'] == 'warning' else "✗"
            print(f"    {status_icon} {finding['category']}: {finding['message']}")
    else:
        print(f"    ✗ Configuration audit failed: {config_audit.error}")
    
    print("[*] Performing key security audit...")
    key_audit = client.security_audit('key', key_data['hex_key'])
    
    if key_audit.success:
        audit_data = key_audit.data
        print(f"    ✓ Key: {audit_data['key_preview']}")
        print(f"    ✓ Overall status: {audit_data['overall_status']}")
        for finding in audit_data['findings']:
            status_icon = "✓" if finding['status'] == 'info' else "⚠" if finding['status'] == 'warning' else "✗"
            print(f"    {status_icon} {finding['category']}: {finding['message']}")
    else:
        print(f"    ✗ Key audit failed: {key_audit.error}")
    
    # Test invalid keys
    print("\n[PHASE 8] Invalid Key Detection")
    print("-" * 40)
    
    invalid_keys = [
        ("Zero key", "0" * 64),
        ("Too large key", "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141"),
        ("Wrong length", "abcd1234"),
        ("Invalid hex", "xyz12345" * 8),
        ("Bad WIF checksum", key_data['wif_key'][:-5] + "XXXXX")
    ]
    
    for name, test_key in invalid_keys:
        key_format = 'wif' if name == "Bad WIF checksum" else 'hex'
        result = client.validate_key(test_key, key_format)
        
        if not result.success:
            print(f"    ✓ {name} correctly detected as invalid: {result.error[:50]}...")
        else:
            print(f"    ✗ {name} incorrectly detected as valid")
    
    # Performance test
    print("\n[PHASE 9] Performance Test")
    print("-" * 40)
    print("[*] Testing key generation performance...")
    
    import time
    start_time = time.time()
    num_keys = 10
    
    valid_keys = 0
    for i in range(num_keys):
        result = client.create_key_pair()
        if result.success:
            valid_keys += 1
    
    total_time = (time.time() - start_time) * 1000
    avg_time = total_time / num_keys
    
    print(f"    ✓ Generated {valid_keys}/{num_keys} valid keys")
    print(f"    ✓ Total time: {total_time:.2f}ms")
    print(f"    ✓ Average time per key: {avg_time:.2f}ms")
    print(f"    ✓ Keys per second: {1000 / avg_time:.1f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("   REFACTORED AUTHENTICATION DEMONSTRATION COMPLETE")
    print("=" * 70)
    
    print("\n[✓] Refactoring Benefits Achieved:")
    print("    • Modular architecture with clear separation of concerns")
    print("    • Dependency injection for better testability")
    print("    • Consistent error handling and logging")
    print("    • Standardized request/response format")
    print("    • Extensible operation registry")
    print("    • Comprehensive security auditing")
    print("    • Batch processing capabilities")
    print("    • Performance monitoring")
    
    print("\n[✓] Key Components:")
    print("    • AuthenticationInterface: Abstract contract for auth operations")
    print("    • AuthenticationConfig: Centralized configuration management")
    print("    • AuthenticationLogger: Structured logging system")
    print("    • Secp256k1Curve: Optimized ECC operations")
    print("    • PrivateKeyValidator: Modular key validation")
    print("    • AuthenticationOrchestrator: Dependency injection coordinator")
    print("    • AuthenticationClient: High-level API interface")
    
    return True


if __name__ == "__main__":
    main()
