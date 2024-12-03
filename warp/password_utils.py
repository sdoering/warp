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
    
    # Generate hash
    hash_bytes = scrypt.hash(password.encode(), salt, N, r, p)
    
    # Encode salt and hash in base64
    salt_b64 = base64.b64encode(salt).decode()
    hash_b64 = base64.b64encode(hash_bytes).decode()
    
    # Format: scrypt:N:r:p$salt$hash
    return f'scrypt:{N}:{r}:{p}${salt_b64}${hash_b64}'
