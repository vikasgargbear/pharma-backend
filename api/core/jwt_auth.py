"""
JWT-based authentication with organization context
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from ..database import get_db

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720  # 12 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token with user and organization context"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_and_org(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Extract user and organization context from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        org_id: str = payload.get("org_id")
        
        if user_id is None or org_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Verify user still exists and is active
    user = db.execute(text("""
        SELECT u.user_id, u.full_name, u.email, u.role, u.org_id,
               o.org_name, o.is_active as org_active
        FROM org_users u
        JOIN organizations o ON u.org_id = o.org_id
        WHERE u.user_id = :user_id 
        AND u.is_active = true
        AND o.org_id = :org_id
    """), {"user_id": user_id, "org_id": org_id}).fetchone()
    
    if user is None:
        raise credentials_exception
    
    if not user.org_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is not active"
        )
    
    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id),
        "org_name": user.org_name
    }

def get_current_org(current_user: Dict = Depends(get_current_user_and_org)) -> Dict[str, Any]:
    """Get current organization context from authenticated user"""
    return {
        "org_id": current_user["org_id"],
        "org_name": current_user["org_name"]
    }

def get_current_user(current_user: Dict = Depends(get_current_user_and_org)) -> Dict[str, Any]:
    """Get current user context from authenticated user"""
    return {
        "user_id": current_user["user_id"],
        "full_name": current_user["full_name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "org_id": current_user["org_id"]
    }

async def verify_user_org_access(
    user_id: int,
    org_id: str,
    db: Session
) -> bool:
    """Verify if a user has access to a specific organization"""
    result = db.execute(text("""
        SELECT COUNT(*) > 0 as has_access
        FROM org_users
        WHERE user_id = :user_id
        AND org_id = :org_id
        AND is_active = true
    """), {"user_id": user_id, "org_id": org_id}).scalar()
    
    return result

def require_role(allowed_roles: list):
    """Dependency to require specific roles"""
    def role_checker(current_user: Dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user['role']}' not authorized. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker

def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_checker(
        current_user: Dict = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Check if user has the required permission
        result = db.execute(text("""
            SELECT permissions->:permission as has_permission
            FROM org_users
            WHERE user_id = :user_id
        """), {
            "user_id": current_user["user_id"],
            "permission": permission
        }).scalar()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker