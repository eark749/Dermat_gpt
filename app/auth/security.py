"""
Security utilities for password hashing and JWT token management.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# Password hashing with PBKDF2 (built-in, no external dependencies)
HASH_ALGORITHM = 'sha256'
HASH_ITERATIONS = 100000

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))  # 7 days default


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA256.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password (format: salt$hash)
    """
    # Generate a random salt
    salt = secrets.token_hex(32)
    
    # Hash the password with the salt
    pwd_hash = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM,
        password.encode('utf-8'),
        salt.encode('utf-8'),
        HASH_ITERATIONS
    )
    
    # Return salt and hash combined
    return f"{salt}${pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database (format: salt$hash)
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        salt, pwd_hash = hashed_password.split('$')
        
        # Hash the provided password with the same salt
        new_hash = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            HASH_ITERATIONS
        )
        
        # Compare hashes (constant-time comparison)
        return secrets.compare_digest(pwd_hash, new_hash.hex())
    except (ValueError, AttributeError):
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token (user_id, username, etc.)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

