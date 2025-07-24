"""
Authentication utilities
Provides get_current_org dependency for routes
"""

from typing import Dict
from fastapi import Depends, HTTPException, status
from uuid import UUID

# Default organization ID used throughout the system
DEFAULT_ORG_ID = "12de5e22-eee7-4d25-b3a7-d16d01c6170f"

def get_current_org() -> Dict[str, UUID]:
    """
    Get the current organization context.
    In a full implementation, this would extract org from JWT token.
    For now, returns the default organization.
    """
    return {
        "org_id": UUID(DEFAULT_ORG_ID),
        "org_name": "Default Pharmacy"
    }

def get_current_user() -> Dict[str, any]:
    """
    Get the current user context.
    In a full implementation, this would extract user from JWT token.
    For now, returns a default user.
    """
    return {
        "user_id": 1,
        "username": "admin",
        "org_id": UUID(DEFAULT_ORG_ID)
    }