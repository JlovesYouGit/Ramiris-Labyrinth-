import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

BIP39_ENGLISH = [
    'abandon', 'ability', 'able', 'about', 'above', 'absent', 'absorb', 'abstract',
    'absurd', 'abuse', 'access', 'accident', 'account', 'accuse', 'achieve', 'acid',
    'acoustic', 'acquire', 'across', 'act', 'action', 'actor', 'actress', 'actual',
    'adapt', 'add', 'addict', 'address', 'adjust', 'admit', 'adult', 'advance',
    'advice', 'aerobic', 'affair', 'afford', 'afraid', 'again', 'age', 'agent',
    'agree', 'ahead', 'aim', 'air', 'airport', 'aisle', 'alarm', 'album',
    'alcohol', 'alert', 'alien', 'all', 'alley', 'allow', 'almost', 'alone',
    'alpha', 'already', 'also', 'alter', 'always', 'amateur', 'amazing', 'among'
]

def generate_mnemonic(strength=256):
    entropy_bytes = strength // 8
    entropy = os.urandom(entropy_bytes)
    entropy_hash = hashlib.sha256(entropy).digest()
    checksum_bits = strength // 32
    checksum = entropy_hash[0] >> (8 - checksum_bits)
    entropy_int = int.from_bytes(entropy, 'big')
    entropy_bits_str = bin(entropy_int)[2:].zfill(strength)
    checksum_binary = bin(checksum)[2:].zfill(checksum_bits)
    total_bits = entropy_bits_str + checksum_binary
    
    indices = []
    for i in range(0, len(total_bits), 11):
        chunk = total_bits[i:i+11]
        index = int(chunk, 2)
        indices.append(index)
    
    words = [BIP39_ENGLISH[i % len(BIP39_ENGLISH)] for i in indices]
    return ' '.join(words)

phrases = []
for strength in [128, 256]:
    phrase = generate_mnemonic(strength)
    word_count = len(phrase.split())
    phrases.append(f'{word_count}-word mnemonic ({strength}-bit entropy):')
    phrases.append(phrase)
    phrases.append('')

cred_name = os.getenv('CRED_NAME', 'cred')
cred_sha1 = os.getenv('CRED_SHA1', '')

with open('recovery_phrase.txt', 'w') as f:
    f.write('BIP39 RECOVERY PHRASES\n')
    f.write('=' * 60 + '\n\n')
    f.write(f'Credential: {cred_name}\n')
    f.write(f'Target: {cred_sha1}\n\n')
    f.write('\n'.join(phrases))

print('Saved to: n:\satoshi\recovery_phrase.txt')
print('\n'.join(phrases))
