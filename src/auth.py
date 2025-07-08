from datetime import datetime, timedelta
from typing import Optional
from jose import jwt

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): Data to encode inside the token (e.g., {"sub": "username"}).
        expires_delta (Optional[timedelta]): Custom expiration time delta. Defaults to 15 minutes if not provided.

    Returns:
        str: Encoded JWT token as a string.
    """
    to_encode = data.copy()

    # Determine expiration time
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
