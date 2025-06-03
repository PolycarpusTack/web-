"""
Compliance and Audit Management API endpoints.
Provides comprehensive audit logging, compliance reporting, and security monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import json
import csv
import io
from fastapi.responses import StreamingResponse

from db.database import get_db
from db.crud import (
    create_audit_log, get_audit_logs, user_has_permission,
    get_user, get_workspace, get_users
)
from .jwt import get_current_user
from .schemas import UserResponse

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# Enhanced audit logging models
class AuditLogFilter(BaseModel):
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    risk_level: Optional[str] = None
    is_suspicious: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    timestamp: datetime
    workspace_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    risk_level: str
    is_suspicious: bool
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    meta_data: Optional[Dict[str, Any]]
    
    # Enriched data
    user_email: Optional[str] = None
    workspace_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ComplianceReport(BaseModel):
    report_type: str
    period_start: datetime
    period_end: datetime
    total_events: int
    high_risk_events: int
    suspicious_events: int
    failed_access_attempts: int
    data_access_events: int
    configuration_changes: int
    user_management_events: int
    
    # Top statistics
    top_users_by_activity: List[Dict[str, Any]]
    top_actions: List[Dict[str, Any]]
    top_risk_events: List[Dict[str, Any]]
    
    # Compliance metrics
    soc2_compliance_score: float
    gdpr_compliance_score: float
    security_score: float

class SecurityAlert(BaseModel):
    id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    status: str  # open, investigating, resolved, false_positive
    
    # Related data
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    audit_log_ids: List[str] = []
    
    # Actions taken
    actions_taken: List[str] = []
    resolved_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class DataRetentionPolicy(BaseModel):
    retention_days: int = Field(ge=30, le=2555)  # 30 days to 7 years
    auto_archive: bool = True
    archive_after_days: int = Field(ge=90, le=365)
    delete_after_days: Optional[int] = Field(None, ge=365)
    
class ComplianceSettings(BaseModel):
    enable_detailed_logging: bool = True
    log_data_access: bool = True
    log_configuration_changes: bool = True
    log_user_management: bool = True
    log_failed_attempts: bool = True
    
    # Alerting settings
    enable_security_alerts: bool = True
    alert_on_suspicious_activity: bool = True
    alert_on_failed_logins: int = 5  # Number of failed attempts before alert
    alert_on_data_export: bool = True
    
    # Retention settings
    retention_policy: DataRetentionPolicy
    
    # Compliance frameworks
    enable_soc2_compliance: bool = False
    enable_gdpr_compliance: bool = False
    enable_hipaa_compliance: bool = False


# Enhanced audit logging with risk assessment
async def create_enhanced_audit_log(
    db: AsyncSession,
    user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    request: Optional[Request] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
):
    """Create an enhanced audit log entry with risk assessment."""
    
    # Risk assessment
    risk_level = "low"
    is_suspicious = False
    
    # High-risk actions
    high_risk_actions = [
        "delete", "export", "download", "share_external", 
        "change_permissions", "create_api_key", "delete_user",
        "change_password", "admin_access", "bulk_delete"
    ]
    
    # Suspicious patterns
    if action in high_risk_actions:
        risk_level = "high"
    elif action.startswith("access_denied"):
        risk_level = "medium"
        # Check for repeated access denials
        if user_id:
            recent_denials = await get_audit_logs(
                db, user_id=user_id, action="access_denied",
                start_date=datetime.utcnow() - timedelta(hours=1),
                limit=10
            )
            if len(recent_denials) >= 3:
                is_suspicious = True
                risk_level = "high"
    
    # Detect unusual activity patterns
    if user_id and request:
        # Check for activity outside normal hours (example: non-business hours)
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Outside 6 AM - 10 PM UTC
            risk_level = "medium"
        
        # Check for unusual IP addresses
        ip_address = request.client.host if request else None
        if ip_address and user_id:
            # Get recent IPs for this user
            recent_logs = await get_audit_logs(
                db, user_id=user_id,
                start_date=datetime.utcnow() - timedelta(days=7),
                limit=50
            )
            recent_ips = {log.ip_address for log in recent_logs if log.ip_address}
            if ip_address not in recent_ips and len(recent_ips) > 0:
                risk_level = "medium"
                meta_data = meta_data or {}
                meta_data["new_ip_detected"] = True
    
    return await create_audit_log(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        workspace_id=workspace_id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        session_id=session_id,
        old_values=old_values,
        new_values=new_values,
        meta_data=meta_data,
        risk_level=risk_level,
        is_suspicious=is_suspicious
    )


# Audit log endpoints
@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs_endpoint(
    filters: AuditLogFilter = Depends(),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with advanced filtering."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "audit.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get audit logs
    logs = await get_audit_logs(
        db=db,
        user_id=filters.user_id,
        workspace_id=filters.workspace_id,
        action=filters.action,
        resource_type=filters.resource_type,
        start_date=filters.start_date,
        end_date=filters.end_date,
        skip=skip,
        limit=limit
    )
    
    # Enrich with user and workspace data
    enriched_logs = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "timestamp": log.timestamp,
            "workspace_id": log.workspace_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "session_id": log.session_id,
            "risk_level": log.risk_level,
            "is_suspicious": log.is_suspicious,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "meta_data": log.meta_data
        }
        
        # Enrich with user data
        if log.user_id:
            user = await get_user(db, log.user_id)
            if user:
                log_dict["user_email"] = user.email
        
        # Enrich with workspace data
        if log.workspace_id:
            workspace = await get_workspace(db, log.workspace_id)
            if workspace:
                log_dict["workspace_name"] = workspace.display_name
        
        enriched_logs.append(AuditLogResponse(**log_dict))
    
    return enriched_logs


@router.get("/audit-logs/export")
async def export_audit_logs(
    format: str = Query("csv", regex="^(csv|json)$"),
    filters: AuditLogFilter = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export audit logs in CSV or JSON format."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "audit.export")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get all matching logs (no pagination for export)
    logs = await get_audit_logs(
        db=db,
        user_id=filters.user_id,
        workspace_id=filters.workspace_id,
        action=filters.action,
        resource_type=filters.resource_type,
        start_date=filters.start_date,
        end_date=filters.end_date,
        skip=0,
        limit=10000  # Reasonable limit for export
    )
    
    # Log the export action
    await create_enhanced_audit_log(
        db=db,
        user_id=current_user.id,
        action="export_audit_logs",
        resource_type="audit_logs",
        meta_data={
            "format": format,
            "total_records": len(logs),
            "filters": filters.dict(exclude_unset=True)
        }
    )
    
    if format == "csv":
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Timestamp", "User ID", "Action", "Resource Type", "Resource ID",
            "Workspace ID", "IP Address", "Risk Level", "Is Suspicious", "User Agent"
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.user_id or "",
                log.action,
                log.resource_type,
                log.resource_id or "",
                log.workspace_id or "",
                log.ip_address or "",
                log.risk_level,
                log.is_suspicious,
                log.user_agent or ""
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    
    elif format == "json":
        # Create JSON
        export_data = []
        for log in logs:
            export_data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "workspace_id": log.workspace_id,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "session_id": log.session_id,
                "risk_level": log.risk_level,
                "is_suspicious": log.is_suspicious,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "meta_data": log.meta_data
            })
        
        json_content = json.dumps(export_data, indent=2, default=str)
        
        return StreamingResponse(
            io.BytesIO(json_content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )


@router.get("/reports/compliance", response_model=ComplianceReport)
async def generate_compliance_report(
    period_days: int = Query(30, ge=1, le=365),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a comprehensive compliance report."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "audit.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get all logs for the period
    all_logs = await get_audit_logs(
        db=db,
        start_date=start_date,
        end_date=end_date,
        skip=0,
        limit=50000  # Large limit for comprehensive analysis
    )
    
    # Calculate metrics
    total_events = len(all_logs)
    high_risk_events = len([log for log in all_logs if log.risk_level == "high"])
    suspicious_events = len([log for log in all_logs if log.is_suspicious])
    failed_access_attempts = len([log for log in all_logs if log.action == "access_denied"])
    data_access_events = len([log for log in all_logs if log.resource_type in ["files", "conversations", "credentials"]])
    configuration_changes = len([log for log in all_logs if log.action in ["update", "create", "delete"] and log.resource_type in ["workspace", "user", "role"]])
    user_management_events = len([log for log in all_logs if log.resource_type == "user"])
    
    # Top users by activity
    user_activity = {}
    for log in all_logs:
        if log.user_id:
            user_activity[log.user_id] = user_activity.get(log.user_id, 0) + 1
    
    top_users = []
    for user_id, count in sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]:
        user = await get_user(db, user_id)
        top_users.append({
            "user_id": user_id,
            "email": user.email if user else "Unknown",
            "activity_count": count
        })
    
    # Top actions
    action_counts = {}
    for log in all_logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
    
    top_actions = [
        {"action": action, "count": count}
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    
    # Top risk events
    risk_events = [log for log in all_logs if log.risk_level in ["high", "medium"] or log.is_suspicious]
    top_risk_events = []
    for log in risk_events[:10]:
        user = await get_user(db, log.user_id) if log.user_id else None
        top_risk_events.append({
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "user_email": user.email if user else "Unknown",
            "risk_level": log.risk_level,
            "is_suspicious": log.is_suspicious,
            "ip_address": log.ip_address
        })
    
    # Calculate compliance scores (simplified scoring)
    soc2_score = min(100, max(0, 100 - (suspicious_events * 5) - (high_risk_events * 2)))
    gdpr_score = min(100, max(0, 100 - (data_access_events * 0.1) - (failed_access_attempts * 2)))
    security_score = min(100, max(0, 100 - (suspicious_events * 10) - (failed_access_attempts * 1)))
    
    # Log report generation
    await create_enhanced_audit_log(
        db=db,
        user_id=current_user.id,
        action="generate_compliance_report",
        resource_type="compliance",
        meta_data={
            "period_days": period_days,
            "total_events": total_events,
            "report_type": "compliance"
        }
    )
    
    return ComplianceReport(
        report_type="compliance",
        period_start=start_date,
        period_end=end_date,
        total_events=total_events,
        high_risk_events=high_risk_events,
        suspicious_events=suspicious_events,
        failed_access_attempts=failed_access_attempts,
        data_access_events=data_access_events,
        configuration_changes=configuration_changes,
        user_management_events=user_management_events,
        top_users_by_activity=top_users,
        top_actions=top_actions,
        top_risk_events=top_risk_events,
        soc2_compliance_score=soc2_score,
        gdpr_compliance_score=gdpr_score,
        security_score=security_score
    )


@router.get("/security/suspicious-activity")
async def get_suspicious_activity(
    hours: int = Query(24, ge=1, le=168),  # Last 1-168 hours
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent suspicious activity for security monitoring."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "audit.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get suspicious logs
    start_date = datetime.utcnow() - timedelta(hours=hours)
    suspicious_logs = await get_audit_logs(
        db=db,
        start_date=start_date,
        skip=0,
        limit=1000
    )
    
    # Filter for suspicious activity
    suspicious_activity = []
    for log in suspicious_logs:
        if log.is_suspicious or log.risk_level == "high" or log.action == "access_denied":
            user = await get_user(db, log.user_id) if log.user_id else None
            workspace = await get_workspace(db, log.workspace_id) if log.workspace_id else None
            
            suspicious_activity.append({
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "resource_type": log.resource_type,
                "user_email": user.email if user else "Unknown",
                "workspace_name": workspace.display_name if workspace else None,
                "ip_address": log.ip_address,
                "risk_level": log.risk_level,
                "is_suspicious": log.is_suspicious,
                "details": log.meta_data
            })
    
    return {
        "period_hours": hours,
        "total_suspicious_events": len(suspicious_activity),
        "events": suspicious_activity
    }


@router.post("/audit-log")
async def manual_audit_log(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Manually create an audit log entry (for application integration)."""
    # Create audit log
    await create_enhanced_audit_log(
        db=db,
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request=request,
        meta_data=meta_data
    )
    
    return {"message": "Audit log entry created successfully"}


@router.get("/stats/overview")
async def get_audit_overview(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get high-level audit statistics overview."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "audit.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get statistics for last 24 hours, 7 days, and 30 days
    now = datetime.utcnow()
    periods = {
        "24h": now - timedelta(hours=24),
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30)
    }
    
    stats = {}
    for period_name, start_date in periods.items():
        logs = await get_audit_logs(db=db, start_date=start_date, limit=50000)
        
        stats[period_name] = {
            "total_events": len(logs),
            "high_risk_events": len([log for log in logs if log.risk_level == "high"]),
            "suspicious_events": len([log for log in logs if log.is_suspicious]),
            "failed_access_attempts": len([log for log in logs if log.action == "access_denied"]),
            "unique_users": len(set(log.user_id for log in logs if log.user_id)),
            "unique_ips": len(set(log.ip_address for log in logs if log.ip_address))
        }
    
    return stats