"""
Decode the Bitcoin genesis block coinbase transaction data
Shows exactly what is in the genesis block - no hidden backdoors
"""

# The genesis block coinbase scriptSig (hex)
# This is the input script of the coinbase transaction
genesis_scriptSig_hex = "04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f722062616e6b73"

print("=" * 60)
print("BITCOIN GENESIS BLOCK COINBASE DECODE")
print("=" * 60)
print()

# Decode the hex
data = bytes.fromhex(genesis_scriptSig_hex)

print("Raw hex:")
print(genesis_scriptSig_hex)
print()

print("Breakdown:")
print("-" * 60)

# Parse the scriptSig structure
# 04 - Push 4 bytes
# ffff001d - Extra nonce / nBits
# 01 - Push 1 byte  
# 04 - Variable length (0x04 = 4 bytes)
# 45 - Push 69 bytes (0x45 = 69)
# The Times 03/Jan/2009 Chancellor on brink of second bailout for banks

pos = 0

# First push: extra nonce / nBits
push1_size = data[pos]
pos += 1
push1_data = data[pos:pos+push1_size]
print(f"Push {push1_size} bytes (extra nonce/nBits): {push1_data.hex()}")
pos += push1_size

# Second push: another small value
push2_size = data[pos]
pos += 1
push2_data = data[pos:pos+push2_size]
print(f"Push {push2_size} byte: {push2_data.hex()}")
pos += push2_size

# Third push: the famous message
push3_size = data[pos]
pos += 1
push3_data = data[pos:pos+push3_size]
print(f"Push {push3_size} bytes (The Times message): {push3_data}")
print(f"  = '{push3_data.decode('utf-8')}'")
pos += push3_size

print()
print("=" * 60)
print("ANALYSIS")
print("=" * 60)
print()
print("What IS there:")
print("  - The Times headline (proof of date)")
print("  - Extra nonce values (mining data)")
print("  - Nothing else")
print()
print("What is NOT there:")
print("  - No private key")
print("  - No public key")
print("  - No backdoor code")
print("  - No 'call method'")
print("  - No hidden instructions")
print()
print("The scriptSig is just data pushes - no executable code that")
print("could reveal a key. It's just the newspaper headline.")
print()

# Show the genesis block output scriptPubKey
print("=" * 60)
print("OUTPUT SCRIPTPUBKEY (where the 50 BTC went)")
print("=" * 60)

# The scriptPubKey for the genesis coinbase output
# This is a standard P2PKH (Pay to Public Key Hash) script
# 76a91462e907b15cbf27d5425399ebf6f0fb50ebb88f1888ac
# 76 = OP_DUP
# a9 = OP_HASH160  
# 14 = Push 20 bytes (the hash160 of the public key)
# 62e907b15cbf27d5425399ebf6f0fb50ebb88f18 = The hash160 (address hash)
# 88 = OP_EQUALVERIFY
# ac = OP_CHECKSIG

scriptPubKey_hex = "76a91462e907b15cbf27d5425399ebf6f0fb50ebb88f1888ac"
print(f"scriptPubKey: {scriptPubKey_hex}")
print()
print("Breakdown:")
print("  76      = OP_DUP")
print("  a9      = OP_HASH160")
print("  14      = Push 20 bytes")
print(f"  {scriptPubKey_hex[6:46]} = HASH160 of public key")
print("  88      = OP_EQUALVERIFY")
print("  ac      = OP_CHECKSIG")
print()
print("This is a standard P2PKH script. It locks the coins to whoever")
print("can provide:")
print("  1. A public key that hashes to the given hash")
print("  2. A signature from that public key")
print()
print("There is NO private key embedded in this script.")
print("There is NO backdoor.")
print("There is NO 'call method'.")
