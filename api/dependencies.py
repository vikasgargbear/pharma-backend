"""
Common dependencies for FastAPI routes

CREATED: This file was missing and causing import errors in multiple routers.
It centralizes authentication and permission checking logic that was previously
referenced from various locations (core.security, auth, etc.)

All routers now import authentication dependencies from this single location.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .database import get_db
from .core.config import settings
from . import models

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Get current active user
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_permission(required_permission: str):
    """
    Check if user has required permission
    """
    async def permission_checker(
        current_user: models.User = Depends(get_current_active_user)
    ):
        # For now, simple role-based check
        # In production, implement proper permission system
        if current_user.role == "admin":
            return current_user
        
        # Add more permission logic here
        role_permissions = {
            "manager": ["read", "write", "update"],
            "sales": ["read", "write"],
            "warehouse": ["read", "update_inventory"],
            "accounts": ["read", "write_payments"]
        }
        
        user_permissions = role_permissions.get(current_user.role, [])
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        return current_user
    
    return permission_checker