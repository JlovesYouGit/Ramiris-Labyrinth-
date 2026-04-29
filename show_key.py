import sys
sys.path.insert(0, 'n:\\satoshi')
from crypto_trigger import PrivateKeyValidator

# Generate a valid key
key = PrivateKeyValidator.generate_valid_key(compressed=True)
print('=== GENERATED PRIVATE KEY ===')
print(f'Hex (64 chars): {key["hex"]}')
print(f'WIF (compressed): {key["wif"]}')
print(f'Compressed: {key["compressed"]}')
print()

# Also generate uncompressed
key_uncomp = PrivateKeyValidator.generate_valid_key(compressed=False)
print('=== UNCOMPRESSED VARIANT ===')
print(f'Hex: {key_uncomp["hex"]}')
print(f'WIF (uncompressed): {key_uncomp["wif"]}')
