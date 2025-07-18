"""
Users Router - All user authentication and management endpoints
Complete user management system with JWT auth, roles, and analytics
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from ..database import get_db
from .. import models, schemas
from ..core.crud_base import create_crud
from ..core.security import handle_database_error
from ..core.config import settings

# Create router
router = APIRouter(prefix="/users", tags=["users"])

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create CRUD instances using our generic system
user_crud = create_crud(models.User)
role_crud = create_crud(models.Role)
permission_crud = create_crud(models.Permission)
user_session_crud = create_crud(models.UserSession)

# ================= AUTHENTICATION =================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = user_crud.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register", response_model=schemas.User)
@handle_database_error
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user.password)
    
    # Create user
    new_user = user_crud.create(db, schemas.UserCreate(**user_dict))
    return new_user

@router.post("/login")
@handle_database_error
def login_user(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """User login"""
    # Get user by email
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id}, expires_delta=access_token_expires
    )
    
    # Create user session
    session_data = {
        "user_id": user.id,
        "session_token": access_token,
        "expires_at": datetime.utcnow() + access_token_expires,
        "is_active": True
    }
    user_session_crud.create(db, schemas.UserSessionCreate(**session_data))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        "user": user
    }

@router.post("/logout")
@handle_database_error
def logout_user(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """User logout"""
    # Deactivate user sessions
    db.query(models.UserSession).filter(
        models.UserSession.user_id == current_user.id,
        models.UserSession.is_active == True
    ).update({"is_active": False})
    db.commit()
    
    return {"message": "Successfully logged out"}

# ================= USER MANAGEMENT =================

@router.get("/me", response_model=schemas.User)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.put("/me", response_model=schemas.User)
@handle_database_error
def update_current_user(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    return user_crud.update(db, db_obj=current_user, obj_in=user_update)

@router.get("/", response_model=List[schemas.User])
@handle_database_error
def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    # Check if user has admin role
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    query = db.query(models.User)
    
    if role:
        query = query.filter(models.User.role == role)
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{user_id}", response_model=schemas.User)
@handle_database_error
def get_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    # Users can only see their own profile, admins can see all
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.User)
@handle_database_error
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_crud.update(db, db_obj=user, obj_in=user_update)

@router.delete("/{user_id}")
@handle_database_error
def delete_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = user_crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_crud.remove(db, id=user_id)
    return {"message": "User deleted successfully"}

# ================= ROLE MANAGEMENT =================

@router.get("/roles/", response_model=List[schemas.Role])
@handle_database_error
def get_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all roles"""
    return role_crud.get_multi(db, skip=skip, limit=limit)

@router.post("/roles/", response_model=schemas.Role)
@handle_database_error
def create_role(
    role: schemas.RoleCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new role (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return role_crud.create(db, role)

# ================= USER ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_user_analytics(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user analytics summary"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Total users
    total_users = db.query(models.User).count()
    
    # Active users
    active_users = db.query(models.User).filter(models.User.is_active == True).count()
    
    # Users by role
    role_counts = db.query(models.User.role, db.func.count(models.User.id)).group_by(models.User.role).all()
    
    # Recent registrations (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = db.query(models.User).filter(
        models.User.created_at >= thirty_days_ago
    ).count()
    
    # Active sessions
    active_sessions = db.query(models.UserSession).filter(
        models.UserSession.is_active == True,
        models.UserSession.expires_at > datetime.utcnow()
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "role_distribution": dict(role_counts),
        "recent_registrations_30d": recent_users,
        "active_sessions": active_sessions,
        "activity_rate": (active_users / total_users * 100) if total_users > 0 else 0
    }

@router.get("/sessions/active")
@handle_database_error
def get_active_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active user sessions"""
    if current_user.role != "admin":
        # Users can only see their own sessions
        sessions = db.query(models.UserSession).filter(
            models.UserSession.user_id == current_user.id,
            models.UserSession.is_active == True,
            models.UserSession.expires_at > datetime.utcnow()
        ).all()
    else:
        # Admins can see all active sessions
        sessions = db.query(models.UserSession).filter(
            models.UserSession.is_active == True,
            models.UserSession.expires_at > datetime.utcnow()
        ).all()
    
    return sessions

@router.post("/change-password")
@handle_database_error
def change_password(
    password_change: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not verify_password(password_change.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    hashed_password = get_password_hash(password_change.new_password)
    current_user.password = hashed_password
    db.commit()
    
    return {"message": "Password changed successfully"} 