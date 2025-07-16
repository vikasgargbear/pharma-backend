"""
Compliance Router - All pharmaceutical regulatory compliance endpoints
Critical for drug licensing, audit trails, and regulatory reporting
Supabase (PostgreSQL) compatible
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy import and_, or_, func, text
import json

from ..database import get_db
from .. import models, schemas, crud
from ..core.crud_base import create_crud
from ..core.security import handle_database_error

# Create router
router = APIRouter(prefix="/compliance", tags=["compliance"])

# Create CRUD instances using our generic system
audit_log_crud = create_crud(models.AuditLog)
license_crud = create_crud(models.License)
regulatory_report_crud = create_crud(models.RegulatoryReport)
compliance_check_crud = create_crud(models.ComplianceCheck)

# ================= AUDIT LOGS =================

@router.post("/audit-logs/", response_model=schemas.AuditLog)
@handle_database_error
def create_audit_log(log: schemas.AuditLogCreate, db: Session = Depends(get_db)):
    """Create a new audit log entry"""
    return audit_log_crud.create(db, log)

@router.get("/audit-logs/", response_model=List[schemas.AuditLog])
@handle_database_error
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering"""
    query = db.query(models.AuditLog)
    
    # Apply filters
    if action:
        query = query.filter(models.AuditLog.action == action)
    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    if start_date:
        query = query.filter(models.AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(models.AuditLog.timestamp <= end_date)
    
    return query.order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/audit-logs/{log_id}", response_model=schemas.AuditLog)
@handle_database_error
def get_audit_log(log_id: int, db: Session = Depends(get_db)):
    """Get specific audit log entry"""
    log = audit_log_crud.get(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return log

# ================= LICENSES =================

@router.post("/licenses/", response_model=schemas.License)
@handle_database_error
def create_license(license: schemas.LicenseCreate, db: Session = Depends(get_db)):
    """Create a new license record"""
    return license_crud.create(db, license)

@router.get("/licenses/", response_model=List[schemas.License])
@handle_database_error
def get_licenses(
    skip: int = 0,
    limit: int = 100,
    license_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    expiring_soon: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get licenses with filtering"""
    query = db.query(models.License)
    
    # Apply filters
    if license_type:
        query = query.filter(models.License.license_type == license_type)
    if is_active is not None:
        query = query.filter(models.License.is_active == is_active)
    if expiring_soon:
        # Licenses expiring within 30 days
        thirty_days_future = date.today() + timedelta(days=30)
        query = query.filter(models.License.expiry_date <= thirty_days_future)
    
    return query.offset(skip).limit(limit).all()

@router.get("/licenses/{license_id}", response_model=schemas.License)
@handle_database_error
def get_license(license_id: int, db: Session = Depends(get_db)):
    """Get specific license"""
    license = license_crud.get(db, license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    return license

@router.put("/licenses/{license_id}", response_model=schemas.License)
@handle_database_error
def update_license(
    license_id: int,
    license_update: schemas.LicenseUpdate,
    db: Session = Depends(get_db)
):
    """Update a license"""
    license = license_crud.get(db, license_id)
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    
    return license_crud.update(db, db_obj=license, obj_in=license_update)

@router.get("/licenses/alerts/expiring")
@handle_database_error
def get_expiring_licenses(
    days: int = Query(30, description="Number of days to check for expiring licenses"),
    db: Session = Depends(get_db)
):
    """Get licenses expiring soon"""
    future_date = date.today() + timedelta(days=days)
    
    expiring_licenses = db.query(models.License).filter(
        models.License.expiry_date <= future_date,
        models.License.is_active == True
    ).all()
    
    return {
        "alert_period_days": days,
        "total_expiring": len(expiring_licenses),
        "licenses": expiring_licenses
    }

# ================= REGULATORY REPORTS =================

@router.post("/reports/", response_model=schemas.RegulatoryReport)
@handle_database_error
def create_regulatory_report(report: schemas.RegulatoryReportCreate, db: Session = Depends(get_db)):
    """Create a new regulatory report"""
    return regulatory_report_crud.create(db, report)

@router.get("/reports/", response_model=List[schemas.RegulatoryReport])
@handle_database_error
def get_regulatory_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get regulatory reports with filtering"""
    query = db.query(models.RegulatoryReport)
    
    if report_type:
        query = query.filter(models.RegulatoryReport.report_type == report_type)
    if status:
        query = query.filter(models.RegulatoryReport.status == status)
    
    return query.order_by(models.RegulatoryReport.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/reports/{report_id}", response_model=schemas.RegulatoryReport)
@handle_database_error
def get_regulatory_report(report_id: int, db: Session = Depends(get_db)):
    """Get specific regulatory report"""
    report = regulatory_report_crud.get(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Regulatory report not found")
    return report

@router.put("/reports/{report_id}/submit")
@handle_database_error
def submit_regulatory_report(report_id: int, db: Session = Depends(get_db)):
    """Submit a regulatory report"""
    report = regulatory_report_crud.get(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Regulatory report not found")
    
    if report.status != "draft":
        raise HTTPException(status_code=400, detail="Can only submit draft reports")
    
    # Update report status
    report.status = "submitted"
    report.submitted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Report submitted successfully", "report": report}

# ================= COMPLIANCE CHECKS =================

@router.post("/checks/", response_model=schemas.ComplianceCheck)
@handle_database_error
def create_compliance_check(check: schemas.ComplianceCheckCreate, db: Session = Depends(get_db)):
    """Create a new compliance check"""
    return compliance_check_crud.create(db, check)

@router.get("/checks/", response_model=List[schemas.ComplianceCheck])
@handle_database_error
def get_compliance_checks(
    skip: int = 0,
    limit: int = 100,
    check_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get compliance checks with filtering"""
    query = db.query(models.ComplianceCheck)
    
    if check_type:
        query = query.filter(models.ComplianceCheck.check_type == check_type)
    if status:
        query = query.filter(models.ComplianceCheck.status == status)
    
    return query.order_by(models.ComplianceCheck.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/checks/{check_id}", response_model=schemas.ComplianceCheck)
@handle_database_error
def get_compliance_check(check_id: int, db: Session = Depends(get_db)):
    """Get specific compliance check"""
    check = compliance_check_crud.get(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")
    return check

@router.put("/checks/{check_id}/resolve")
@handle_database_error
def resolve_compliance_check(
    check_id: int,
    resolution: schemas.ComplianceResolution,
    db: Session = Depends(get_db)
):
    """Resolve a compliance check"""
    check = compliance_check_crud.get(db, check_id)
    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")
    
    if check.status != "pending":
        raise HTTPException(status_code=400, detail="Can only resolve pending checks")
    
    # Update check status
    check.status = "resolved"
    check.resolution_notes = resolution.notes
    check.resolved_by = resolution.resolved_by
    check.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Compliance check resolved successfully", "check": check}

# ================= COMPLIANCE ANALYTICS =================

@router.get("/analytics/summary")
@handle_database_error
def get_compliance_analytics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get compliance analytics summary"""
    # Set default date range (last 30 days)
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # Get audit logs in date range
    audit_logs = db.query(models.AuditLog).filter(
        models.AuditLog.timestamp >= start_date,
        models.AuditLog.timestamp <= end_date
    ).all()
    
    # Get compliance checks
    compliance_checks = db.query(models.ComplianceCheck).filter(
        models.ComplianceCheck.created_at >= start_date,
        models.ComplianceCheck.created_at <= end_date
    ).all()
    
    # Get licenses
    active_licenses = db.query(models.License).filter(models.License.is_active == True).count()
    expiring_licenses = db.query(models.License).filter(
        models.License.expiry_date <= date.today() + timedelta(days=30),
        models.License.is_active == True
    ).count()
    
    # Calculate metrics
    total_audit_logs = len(audit_logs)
    total_compliance_checks = len(compliance_checks)
    pending_checks = len([c for c in compliance_checks if c.status == "pending"])
    resolved_checks = len([c for c in compliance_checks if c.status == "resolved"])
    
    # Action distribution
    action_counts = {}
    for log in audit_logs:
        action = log.action
        if action not in action_counts:
            action_counts[action] = 0
        action_counts[action] += 1
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "audit_logs": {
            "total": total_audit_logs,
            "action_distribution": action_counts
        },
        "compliance_checks": {
            "total": total_compliance_checks,
            "pending": pending_checks,
            "resolved": resolved_checks,
            "resolution_rate": (resolved_checks / total_compliance_checks * 100) if total_compliance_checks > 0 else 0
        },
        "licenses": {
            "active": active_licenses,
            "expiring_soon": expiring_licenses
        }
    }

@router.get("/analytics/audit-trail")
@handle_database_error
def get_audit_trail_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get audit trail analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get audit logs
    audit_logs = db.query(models.AuditLog).filter(
        models.AuditLog.timestamp >= start_date
    ).all()
    
    # Calculate metrics
    total_actions = len(audit_logs)
    unique_users = len(set(log.user_id for log in audit_logs if log.user_id))
    
    # Daily activity
    daily_activity = {}
    for log in audit_logs:
        day_key = log.timestamp.date().isoformat()
        if day_key not in daily_activity:
            daily_activity[day_key] = 0
        daily_activity[day_key] += 1
    
    # Most active users
    user_activity = {}
    for log in audit_logs:
        if log.user_id:
            if log.user_id not in user_activity:
                user_activity[log.user_id] = 0
            user_activity[log.user_id] += 1
    
    # Sort users by activity
    top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "period_days": days,
        "total_actions": total_actions,
        "unique_users": unique_users,
        "daily_activity": daily_activity,
        "top_users": top_users,
        "avg_actions_per_day": total_actions / days if days > 0 else 0
    }

# ================= REGULATORY COMPLIANCE REPORTS =================

@router.get("/reports/generate/monthly")
@handle_database_error
def generate_monthly_compliance_report(
    year: int = Query(..., description="Year for the report"),
    month: int = Query(..., description="Month for the report (1-12)"),
    db: Session = Depends(get_db)
):
    """Generate monthly compliance report"""
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get data for the month
    audit_logs = db.query(models.AuditLog).filter(
        models.AuditLog.timestamp >= start_date,
        models.AuditLog.timestamp <= end_date
    ).all()
    
    compliance_checks = db.query(models.ComplianceCheck).filter(
        models.ComplianceCheck.created_at >= start_date,
        models.ComplianceCheck.created_at <= end_date
    ).all()
    
    # Calculate metrics
    total_transactions = len(audit_logs)
    critical_actions = len([log for log in audit_logs if log.action in ["DELETE", "UPDATE", "ADMIN_ACTION"]])
    
    # Compliance score calculation
    total_checks = len(compliance_checks)
    passed_checks = len([c for c in compliance_checks if c.status == "resolved"])
    compliance_score = (passed_checks / total_checks * 100) if total_checks > 0 else 100
    
    return {
        "report_period": {
            "year": year,
            "month": month,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "total_transactions": total_transactions,
            "critical_actions": critical_actions,
            "compliance_checks": total_checks,
            "compliance_score": compliance_score
        },
        "audit_summary": {
            "total_logs": len(audit_logs),
            "unique_users": len(set(log.user_id for log in audit_logs if log.user_id)),
            "action_types": len(set(log.action for log in audit_logs))
        },
        "compliance_status": {
            "checks_performed": total_checks,
            "checks_passed": passed_checks,
            "checks_failed": total_checks - passed_checks,
            "pass_rate": compliance_score
        }
    }

@router.get("/reports/drug-licensing")
@handle_database_error
def get_drug_licensing_report(db: Session = Depends(get_db)):
    """Get drug licensing compliance report"""
    # Get all drug-related licenses
    drug_licenses = db.query(models.License).filter(
        models.License.license_type.in_(["DRUG_LICENSE", "WHOLESALE_LICENSE", "RETAIL_LICENSE"])
    ).all()
    
    # Calculate metrics
    total_licenses = len(drug_licenses)
    active_licenses = len([l for l in drug_licenses if l.is_active])
    expiring_licenses = len([
        l for l in drug_licenses 
        if l.expiry_date and l.expiry_date <= date.today() + timedelta(days=30)
    ])
    
    # Group by license type
    license_by_type = {}
    for license in drug_licenses:
        license_type = license.license_type
        if license_type not in license_by_type:
            license_by_type[license_type] = {"active": 0, "expired": 0, "expiring": 0}
        
        if license.is_active:
            if license.expiry_date and license.expiry_date <= date.today() + timedelta(days=30):
                license_by_type[license_type]["expiring"] += 1
            else:
                license_by_type[license_type]["active"] += 1
        else:
            license_by_type[license_type]["expired"] += 1
    
    return {
        "summary": {
            "total_licenses": total_licenses,
            "active_licenses": active_licenses,
            "expiring_licenses": expiring_licenses,
            "compliance_rate": (active_licenses / total_licenses * 100) if total_licenses > 0 else 0
        },
        "license_distribution": license_by_type,
        "recommendations": [
            f"Renew {expiring_licenses} licenses expiring in next 30 days" if expiring_licenses > 0 else "All licenses are current",
            "Schedule quarterly compliance review",
            "Update license documentation"
        ]
    }

@router.post("/reports/audit-export")
@handle_database_error
def export_audit_report(
    export_request: schemas.AuditExportRequest,
    db: Session = Depends(get_db)
):
    """Export audit report for external compliance"""
    # Get audit logs based on request
    query = db.query(models.AuditLog)
    
    if export_request.start_date:
        query = query.filter(models.AuditLog.timestamp >= export_request.start_date)
    if export_request.end_date:
        query = query.filter(models.AuditLog.timestamp <= export_request.end_date)
    if export_request.user_id:
        query = query.filter(models.AuditLog.user_id == export_request.user_id)
    
    audit_logs = query.order_by(models.AuditLog.timestamp.desc()).all()
    
    # Format for export
    export_data = []
    for log in audit_logs:
        export_data.append({
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details
        })
    
    return {
        "export_metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "record_count": len(export_data),
            "date_range": {
                "start": export_request.start_date.isoformat() if export_request.start_date else None,
                "end": export_request.end_date.isoformat() if export_request.end_date else None
            }
        },
        "audit_records": export_data
    } 