from datetime import datetime, timedelta
from typing import Dict, Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from product_evaluator.config import settings
from product_evaluator.models.user.user_model import User
from product_evaluator.utils.database import get_db
from product_evaluator.utils.logger import log_info, log_error

# OAuth2 token URL (used by the client to get an access token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def create_access_token(data: Dict[str, Union[str, datetime]], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        data: Dictionary containing the claims to be encoded in the JWT
        expires_delta: Optional override for token expiration time
        
    Returns:
        JWT token as a string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Encode and return token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username/email and password.
    
    Args:
        db: Database session
        username: Username or email
        password: Plain text password
        
    Returns:
        User if authenticated, None otherwise
    """
    # Check if username is actually an email
    if "@" in username:
        user = db.query(User).filter(User.email == username).first()
    else:
        user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return None
    
    if not user.is_active:
        log_info(f"Inactive user attempted login: {username}")
        return None
    
    if not user.verify_password(password):
        log_info(f"Failed login attempt for user: {username}")
        return None
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the token.
    
    Args:
        token: JWT token from OAuth2 scheme
        db: Database session
        
    Returns:
        User if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except jwt.PyJWTError as e:
        log_error(f"JWT validation error: {str(e)}")
        raise credentials_exception
    
    # Get the user from the database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        log_error(f"User not found for ID: {user_id}")
        raise credentials_exception
        
    if not user.is_active:
        log_error(f"Inactive user attempted to use token: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user account"
        )
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current admin user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User if admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin privileges required"
        )
    return current_user