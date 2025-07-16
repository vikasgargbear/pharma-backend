"""
Audit logging system for tracking user actions and system events
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("logs/audit.log")
audit_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


class AuditLogger:
    """Centralized audit logging"""
    
    @staticmethod
    def log_api_access(
        request: Request,
        user_id: Optional[int] = None,
        response_status: int = 200,
        execution_time: float = 0.0
    ):
        """Log API access attempts"""
        audit_data = {
            "event_type": "api_access",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "ip_address": request.client.host,
            "method": request.method,
            "endpoint": str(request.url.path),
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "response_status": response_status,
            "execution_time_ms": round(execution_time * 1000, 2)
        }
        
        audit_logger.info(json.dumps(audit_data))
    
    @staticmethod
    def log_data_change(
        action: str,
        table_name: str,
        record_id: int,
        user_id: Optional[int] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        ip_address: Optional[str] = None
    ):
        """Log data modifications"""
        audit_data = {
            "event_type": "data_change",
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,  # CREATE, UPDATE, DELETE
            "table_name": table_name,
            "record_id": record_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "old_values": old_values,
            "new_values": new_values
        }
        
        audit_logger.info(json.dumps(audit_data))
    
    @staticmethod
    def log_authentication(
        event: str,
        username: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None
    ):
        """Log authentication events"""
        audit_data = {
            "event_type": "authentication",
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,  # LOGIN, LOGOUT, PASSWORD_CHANGE, etc.
            "username": username,
            "user_id": user_id,
            "ip_address": ip_address,
            "success": success,
            "failure_reason": failure_reason
        }
        
        audit_logger.info(json.dumps(audit_data))
    
    @staticmethod
    def log_security_event(
        event: str,
        description: str,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
        severity: str = "medium"
    ):
        """Log security-related events"""
        audit_data = {
            "event_type": "security",
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "description": description,
            "ip_address": ip_address,
            "user_id": user_id,
            "severity": severity
        }
        
        audit_logger.warning(json.dumps(audit_data))
    
    @staticmethod
    def log_system_event(
        event: str,
        description: str,
        metadata: Optional[Dict] = None
    ):
        """Log system events"""
        audit_data = {
            "event_type": "system",
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "description": description,
            "metadata": metadata or {}
        }
        
        audit_logger.info(json.dumps(audit_data))