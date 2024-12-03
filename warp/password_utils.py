import os
import base64
import scrypt

def generate_password_hash(password):
    """Generate a scrypt hash for the given password"""
    # Use consistent parameters with existing hash
    N = 32768  # 2^15
    r = 8
    p = 1
    
    # Generate a random salt
    salt = os.urandom(16)
    
    # Generate hash using UTF-8 encoded password
    hash_bytes = scrypt.hash(password.encode('utf-8'), salt, N, r, p)
    
    # Encode salt and hash in base64
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    hash_b64 = base64.b64encode(hash_bytes).decode('utf-8')
    
    # Format: scrypt:N:r:p$salt$hash
    return f'scrypt:{N}:{r}:{p}${salt_b64}${hash_b64}'
