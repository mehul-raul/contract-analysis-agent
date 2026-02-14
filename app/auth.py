from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status  # ADD THIS
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # ADD THIS
from sqlalchemy.orm import Session 
from app.database import get_db, Contract, ContractChunk, User

# Add this at the top with other imports
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-change-this-in-production"  # We'll move to .env later
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    """
    Convert plain password to hashed password
    
    Example:
        "mypassword123" → "$2b$12$KIX..."
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if password is correct
    
    Example:
        verify_password("mypassword123", "$2b$12$KIX...") → True
        verify_password("wrongpass", "$2b$12$KIX...") → False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Create JWT token
    
    Example:
        create_access_token({"user_id": 1})
        → "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and extract data
    
    Example:
        verify_token("eyJhbGci...") → {"user_id": 1}
        verify_token("invalid") → None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    Verify JWT token and return user_id
    
    Returns:
        user_id (int)
    """
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user_id from token
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return user_id 