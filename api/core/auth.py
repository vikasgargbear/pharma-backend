"""
Authentication utilities
Provides get_current_org dependency for routes

This module provides backward compatibility while transitioning to JWT auth.
For new code, use jwt_auth.py instead.
"""

from typing import Dict
from fastapi import Depends, HTTPException, status
from uuid import UUID
import os

# Try to import JWT auth, fall back to defaults if not available
try:
    from .jwt_auth import get_current_org as jwt_get_current_org
    from .jwt_auth import get_current_user as jwt_get_current_user
    USE_JWT_AUTH = True
except ImportError:
    USE_JWT_AUTH = False

# Default organization ID used throughout the system
DEFAULT_ORG_ID = os.getenv("DEFAULT_ORG_ID", "12de5e22-eee7-4d25-b3a7-d16d01c6170f")

def get_current_org() -> Dict[str, UUID]:
    """
    Get the current organization context.
    Uses JWT auth if available, otherwise returns default.
    """
    if USE_JWT_AUTH and os.getenv("ENABLE_JWT_AUTH", "false").lower() == "true":
        try:
            return jwt_get_current_org()
        except:
            # Fall back to default if JWT auth fails
            pass
    
    return {
        "org_id": UUID(DEFAULT_ORG_ID),
        "org_name": "Default Pharmacy"
    }

def get_current_user() -> Dict[str, any]:
    """
    Get the current user context.
    Uses JWT auth if available, otherwise returns default.
    """
    if USE_JWT_AUTH and os.getenv("ENABLE_JWT_AUTH", "false").lower() == "true":
        try:
            return jwt_get_current_user()
        except:
            # Fall back to default if JWT auth fails
            pass
    
    return {
        "user_id": 1,
        "username": "admin",
        "org_id": UUID(DEFAULT_ORG_ID)
    }