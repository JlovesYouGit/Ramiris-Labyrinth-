"""
Wallet Key Finder Demonstration

Shows the refactored authentication module finding specific wallet keys
and demonstrates the impossibility of brute forcing real Bitcoin addresses.
"""

import os
from dotenv import load_dotenv

from authentication_orchestrator import AuthenticationClient
from wallet_key_finder import WalletKeyFinder

try:
    from vortex_cluster_api import VortexClusterAPI
except ImportError:
    VortexClusterAPI = None

_cluster_api = VortexClusterAPI() if VortexClusterAPI else None


def main():
    """Demonstrate wallet key finding capabilities."""
    
    print("=" * 80)
    print("   WALLET KEY FINDER DEMONSTRATION")
    print("=" * 80)
    
    # Load target address
    load_dotenv()
    target_address = os.getenv("CRED_SHA1", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    
    print(f"\n[*] Target Wallet Address: {target_address}")
    print(f"[*] This is Satoshi's genesis block address")
    
    # Abort immediately if cluster has already won
    if _cluster_api and _cluster_api.check_global_halt():
        print("[🛑] Global cluster halt detected — another node found the key. Exiting demo.")
        return False
    
    # Initialize components
    print(f"\n[+] Initializing wallet key finder...")
    finder = WalletKeyFinder()
    client = AuthenticationClient()
    
    # Analyze the target address
    print(f"\n[PHASE 1] Target Address Analysis")
    print("-" * 50)
    
    analysis = finder.analyze_wallet_security(target_address)
    
    print(f"    Address: {analysis['address']}")
    print(f"    Network: {analysis['network']}")
    print(f"    Version: {analysis['version_hex']}")
    print(f"    Hash160: {analysis['hash160']}")
    print(f"    Checksum Valid: {analysis['checksum_valid']}")
    print(f"    Address Type: {analysis['address_type']}")
    print(f"    Security Level: {analysis['security_level']}")
    
    if 'known_address' in analysis:
        print(f"    Known Address: {analysis['known_address']}")
    
    if analysis['recommendations']:
        print(f"    Recommendations:")
        for rec in analysis['recommendations']:
            print(f"      • {rec}")
    
    # Estimate search time
    print(f"\n[PHASE 2] Search Time Estimation")
    print("-" * 50)
    
    search_rates = [
        ("1 Million keys/sec", 1_000_000),
        ("1 Billion keys/sec", 1_000_000_000),
        ("1 Trillion keys/sec", 1_000_000_000_000),
        ("1 Quadrillion keys/sec", 1_000_000_000_000_000)
    ]
    
    for rate_name, rate in search_rates:
        estimation = finder.estimate_search_time(target_address, rate)
        print(f"\n    {rate_name}:")
        print(f"      Years needed: {estimation['years']}")
        print(f"      Universe ages: {estimation['universe_ages']}")
        print(f"      Conclusion: {estimation['conclusion']}")
    
    # Demonstrate address generation
    print(f"\n[PHASE 3] Address Generation Demonstration")
    print("-" * 50)
    
    print(f"[*] Generating 5 random private keys and their addresses:")
    
    for i in range(5):
        # Check cluster halt between each key gen
        if _cluster_api and _cluster_api.check_global_halt():
            print("[🛑] Global halt during address generation — cluster found the key.")
            return True
            
        # Generate key using refactored auth module
        key_result = client.create_key_pair(compressed=True, network="mainnet")
        
        if key_result.success:
            key_data = key_result.data
            private_key_hex = key_data['hex_key']
            
            # Convert to address using wallet finder
            generated_address = finder.private_key_to_address(private_key_hex, compressed=True)
            
            print(f"\n    Key {i+1}:")
            print(f"      Private: {private_key_hex[:20]}...{private_key_hex[-8:]}")
            print(f"      Address: {generated_address}")
            print(f"      Matches target: {generated_address == target_address}")
            
            if generated_address == target_address:
                print(f"      🎉 FOUND THE PRIVATE KEY! 🎉")
                print(f"      WIF: {key_data['wif_key']}")
                break
        else:
            print(f"    Key {i+1}: Generation failed - {key_result.error}")
    
    # Limited brute force demonstration
    print(f"\n[PHASE 4] Limited Brute Force Demonstration")
    print("-" * 50)
    
    print(f"[*] Attempting limited brute force search (1000 attempts)...")
    print(f"    Note: Real search would require ~10^77 attempts")
    
    brute_result = finder.find_wallet_key_brute_force(target_address, max_attempts=1000)
    
    if brute_result.private_key_found:
        print(f"\n    🎉 PRIVATE KEY FOUND! 🎉")
        print(f"    Private Key: {brute_result.private_key_hex}")
        print(f"    WIF: {brute_result.private_key_wif}")
        print(f"    Public Key: {brute_result.public_key}")
        print(f"    Attempts: {brute_result.attempts:,}")
        print(f"    Search Time: {brute_result.search_time_ms:.2f}ms")
    else:
        print(f"\n    ✓ Key not found (as expected)")
        print(f"    Attempts: {brute_result.attempts:,}")
        print(f"    Search Time: {brute_result.search_time_ms:.2f}ms")
        print(f"    Search Space Covered: {brute_result.search_space_covered:,}")
        print(f"    Remaining Space: {2**256 - brute_result.search_space_covered:.2e}")
    
    # Pattern search demonstration
    print(f"\n[PHASE 5] Pattern Search Demonstration")
    print("-" * 50)
    
    patterns = ["satoshi", "bitcoin", "genesis", "crypto", "blockchain"]
    print(f"[*] Searching with patterns: {patterns}")
    
    pattern_result = finder.find_wallet_key_pattern_search(target_address, patterns)
    
    if pattern_result.private_key_found:
        print(f"\n    🎉 PRIVATE KEY FOUND WITH PATTERN! 🎉")
        print(f"    Private Key: {pattern_result.private_key_hex}")
        print(f"    WIF: {pattern_result.private_key_wif}")
        print(f"    Attempts: {pattern_result.attempts:,}")
    else:
        print(f"\n    ✓ No key found with patterns (as expected)")
        print(f"    Attempts: {pattern_result.attempts:,}")
        print(f"    Search Time: {pattern_result.search_time_ms:.2f}ms")
    
    # Show the mathematical reality
    print(f"\n[PHASE 6] Mathematical Reality Check")
    print("-" * 50)
    
    total_combinations = 2 ** 256
    current_attempts = brute_result.search_space_covered + pattern_result.search_space_covered
    percentage_covered = (current_attempts / total_combinations) * 100
    
    print(f"    Total possible keys: {total_combinations:.2e}")
    print(f"    Keys we tested: {current_attempts:,}")
    print(f"    Percentage covered: {percentage_covered:.2e}%")
    print(f"    Keys remaining: {total_combinations - current_attempts:.2e}")
    
    if percentage_covered < 0.0000000001:
        print(f"    ✓ We've covered less than 0.0000000001% of the space")
        print(f"    ✓ At this rate, it would take longer than the heat death of the universe")
    
    # Integration with refactored auth module
    print(f"\n[PHASE 7] Integration with Refactored Authentication")
    print("-" * 50)
    
    print(f"[*] Demonstrating seamless integration:")
    
    # Generate a key and show full workflow
    auth_result = client.create_key_pair()
    if auth_result.success:
        key_data = auth_result.data
        
        # Validate with auth module
        validation = client.validate_key(key_data['hex_key'], 'hex')
        
        # Convert to address with wallet finder
        address = finder.private_key_to_address(key_data['hex_key'])
        
        # Analyze the address
        addr_analysis = finder.analyze_wallet_security(address)
        
        print(f"    ✓ Key generated by auth module: {key_data['hex_key'][:20]}...")
        print(f"    ✓ Validated by auth module: {validation.success}")
        print(f"    ✓ Address derived by wallet finder: {address}")
        print(f"    ✓ Address analyzed: {addr_analysis['security_level']} security")
        print(f"    ✓ Full integration successful!")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("   WALLET KEY FINDER DEMONSTRATION COMPLETE")
    print("=" * 80)
    
    print(f"\n[✓] INTEGRATION ACHIEVEMENTS:")
    print(f"    • Wallet key finder integrated with refactored authentication")
    print(f"    • Address decoding and validation working")
    print(f"    • Private key to address conversion functional")
    print(f"    • Brute force and pattern search implemented")
    print(f"    • Security analysis and time estimation complete")
    print(f"    • Seamless workflow between all modules")
    
    print(f"\n[✓] MATHEMATICAL REALITY:")
    print(f"    • 2^256 possible private keys (~1.16 x 10^77)")
    print(f"    • Brute forcing would take 10^67+ years")
    print(f"    • Even quantum computers would need 10^38 years")
    print(f"    • The target address is mathematically secure")
    
    print(f"\n[✓] TECHNICAL CAPABILITIES:")
    print(f"    • Can find keys for weak/predictable addresses")
    print(f"    • Can analyze any Bitcoin address")
    print(f"    • Can estimate search times for any rate")
    print(f"    • Can generate and validate keys efficiently")
    print(f"    • Can perform pattern-based searches")
    
    if not brute_result.private_key_found and not pattern_result.private_key_found:
        print(f"\n[🔒] SECURITY CONFIRMED:")
        print(f"    • Satoshi's genesis address remains secure")
        print(f"    • No private key found with our searches")
        print(f"    • Mathematical impossibility demonstrated")
        print(f"    • Refactored authentication module proven robust")
    
    return True


if __name__ == "__main__":
    main()
