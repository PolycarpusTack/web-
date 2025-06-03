"""
Security Monitoring Service
Real-time security threat detection and alerting system.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from db.database import async_session_maker
from db.crud import get_audit_logs, get_user, create_audit_log

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    BRUTE_FORCE = "brute_force"
    UNUSUAL_ACCESS = "unusual_access"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_LOCATION = "suspicious_location"
    MASS_DELETION = "mass_deletion"
    UNAUTHORIZED_API_ACCESS = "unauthorized_api_access"


@dataclass
class SecurityAlert:
    id: str
    threat_type: ThreatType
    severity: AlertSeverity
    title: str
    description: str
    user_id: Optional[str]
    workspace_id: Optional[str]
    detected_at: datetime
    evidence: List[Dict[str, Any]]
    recommended_actions: List[str]
    auto_resolved: bool = False


class SecurityMonitor:
    """Main security monitoring service."""
    
    def __init__(self):
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.threat_detectors = [
            BruteForceDetector(),
            UnusualAccessDetector(),
            DataExfiltrationDetector(),
            PrivilegeEscalationDetector(),
            MassDeletionDetector(),
            UnauthorizedAPIAccessDetector()
        ]
    
    async def analyze_recent_activity(self, minutes: int = 5) -> List[SecurityAlert]:
        """Analyze recent activity for security threats."""
        alerts = []
        
        async with async_session_maker() as db:
            # Get recent audit logs
            start_time = datetime.utcnow() - timedelta(minutes=minutes)
            recent_logs = await get_audit_logs(
                db=db,
                start_date=start_time,
                limit=1000
            )
            
            # Run each threat detector
            for detector in self.threat_detectors:
                try:
                    detected_alerts = await detector.detect(db, recent_logs)
                    alerts.extend(detected_alerts)
                except Exception as e:
                    logger.error(f"Error in {detector.__class__.__name__}: {e}")
        
        # Store new alerts
        for alert in alerts:
            self.active_alerts[alert.id] = alert
            
        return alerts
    
    async def get_active_alerts(self) -> List[SecurityAlert]:
        """Get all active security alerts."""
        return list(self.active_alerts.values())
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Mark an alert as resolved."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            return True
        return False


class ThreatDetector:
    """Base class for threat detectors."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        """Detect threats in audit logs."""
        raise NotImplementedError


class BruteForceDetector(ThreatDetector):
    """Detects brute force login attempts."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        alerts = []
        
        # Group failed login attempts by user and IP
        failed_attempts = {}
        for log in logs:
            if log.action == "access_denied" and "login" in str(log.meta_data).lower():
                key = (log.user_id or log.ip_address, log.ip_address)
                if key not in failed_attempts:
                    failed_attempts[key] = []
                failed_attempts[key].append(log)
        
        # Check for brute force patterns
        for (user_id, ip), attempts in failed_attempts.items():
            if len(attempts) >= 5:  # 5+ failed attempts
                user = await get_user(db, user_id) if user_id else None
                
                alerts.append(SecurityAlert(
                    id=f"bf_{user_id or ip}_{datetime.utcnow().timestamp()}",
                    threat_type=ThreatType.BRUTE_FORCE,
                    severity=AlertSeverity.HIGH,
                    title="Brute Force Attack Detected",
                    description=f"Multiple failed login attempts detected from IP {ip}",
                    user_id=user_id,
                    workspace_id=None,
                    detected_at=datetime.utcnow(),
                    evidence=[{
                        "failed_attempts": len(attempts),
                        "ip_address": ip,
                        "user_email": user.email if user else "Unknown",
                        "time_window": "5 minutes"
                    }],
                    recommended_actions=[
                        "Block IP address temporarily",
                        "Require additional authentication",
                        "Notify user of suspicious activity",
                        "Review IP reputation"
                    ]
                ))
        
        return alerts


class UnusualAccessDetector(ThreatDetector):
    """Detects unusual access patterns."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        alerts = []
        
        # Check for access outside normal hours
        for log in logs:
            if log.user_id and log.action in ["login", "api_access"]:
                hour = log.timestamp.hour
                # Outside 6 AM - 10 PM UTC (adjust for your timezone)
                if hour < 6 or hour > 22:
                    user = await get_user(db, log.user_id)
                    
                    alerts.append(SecurityAlert(
                        id=f"ua_{log.user_id}_{log.timestamp.timestamp()}",
                        threat_type=ThreatType.UNUSUAL_ACCESS,
                        severity=AlertSeverity.MEDIUM,
                        title="Unusual Access Time Detected",
                        description=f"User accessed system outside normal hours",
                        user_id=log.user_id,
                        workspace_id=log.workspace_id,
                        detected_at=datetime.utcnow(),
                        evidence=[{
                            "access_time": log.timestamp.isoformat(),
                            "user_email": user.email if user else "Unknown",
                            "ip_address": log.ip_address,
                            "action": log.action
                        }],
                        recommended_actions=[
                            "Verify user identity",
                            "Check if access was authorized",
                            "Review recent user activity"
                        ]
                    ))
        
        return alerts


class DataExfiltrationDetector(ThreatDetector):
    """Detects potential data exfiltration."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        alerts = []
        
        # Group export/download actions by user
        export_actions = {}
        for log in logs:
            if log.action in ["export", "download", "bulk_export"] and log.user_id:
                if log.user_id not in export_actions:
                    export_actions[log.user_id] = []
                export_actions[log.user_id].append(log)
        
        # Check for unusual export volumes
        for user_id, exports in export_actions.items():
            if len(exports) >= 3:  # 3+ exports in 5 minutes
                user = await get_user(db, user_id)
                
                alerts.append(SecurityAlert(
                    id=f"de_{user_id}_{datetime.utcnow().timestamp()}",
                    threat_type=ThreatType.DATA_EXFILTRATION,
                    severity=AlertSeverity.HIGH,
                    title="Potential Data Exfiltration Detected",
                    description=f"Multiple data export actions detected",
                    user_id=user_id,
                    workspace_id=None,
                    detected_at=datetime.utcnow(),
                    evidence=[{
                        "export_count": len(exports),
                        "user_email": user.email if user else "Unknown",
                        "exported_resources": [e.resource_type for e in exports],
                        "time_window": "5 minutes"
                    }],
                    recommended_actions=[
                        "Review exported data",
                        "Contact user to verify intent",
                        "Check data sensitivity",
                        "Consider temporary access restrictions"
                    ]
                ))
        
        return alerts


class PrivilegeEscalationDetector(ThreatDetector):
    """Detects privilege escalation attempts."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        alerts = []
        
        # Check for role/permission changes
        for log in logs:
            if log.action in ["assign_role", "assign_permission", "update_permissions"] and log.user_id:
                # Check if user is assigning themselves elevated privileges
                if log.new_values and log.user_id == log.new_values.get("target_user_id"):
                    user = await get_user(db, log.user_id)
                    
                    alerts.append(SecurityAlert(
                        id=f"pe_{log.user_id}_{log.timestamp.timestamp()}",
                        threat_type=ThreatType.PRIVILEGE_ESCALATION,
                        severity=AlertSeverity.HIGH,
                        title="Privilege Escalation Attempt",
                        description=f"User attempted to elevate their own privileges",
                        user_id=log.user_id,
                        workspace_id=log.workspace_id,
                        detected_at=datetime.utcnow(),
                        evidence=[{
                            "user_email": user.email if user else "Unknown",
                            "action": log.action,
                            "changes": log.new_values,
                            "ip_address": log.ip_address
                        }],
                        recommended_actions=[
                            "Revoke unauthorized permissions",
                            "Investigate user intent",
                            "Review privilege assignment logs",
                            "Strengthen privilege controls"
                        ]
                    ))
        
        return alerts


class MassDeletionDetector(ThreatDetector):
    """Detects mass deletion events."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        alerts = []
        
        # Group deletion actions by user
        deletion_actions = {}
        for log in logs:
            if log.action == "delete" and log.user_id:
                if log.user_id not in deletion_actions:
                    deletion_actions[log.user_id] = []
                deletion_actions[log.user_id].append(log)
        
        # Check for mass deletions
        for user_id, deletions in deletion_actions.items():
            if len(deletions) >= 5:  # 5+ deletions in 5 minutes
                user = await get_user(db, user_id)
                
                alerts.append(SecurityAlert(
                    id=f"md_{user_id}_{datetime.utcnow().timestamp()}",
                    threat_type=ThreatType.MASS_DELETION,
                    severity=AlertSeverity.CRITICAL,
                    title="Mass Deletion Event Detected",
                    description=f"Multiple deletion actions detected",
                    user_id=user_id,
                    workspace_id=None,
                    detected_at=datetime.utcnow(),
                    evidence=[{
                        "deletion_count": len(deletions),
                        "user_email": user.email if user else "Unknown",
                        "deleted_resources": [d.resource_type for d in deletions],
                        "time_window": "5 minutes"
                    }],
                    recommended_actions=[
                        "Immediately suspend user account",
                        "Check backup systems",
                        "Investigate deletion intent",
                        "Review deleted data recovery options"
                    ]
                ))
        
        return alerts


class UnauthorizedAPIAccessDetector(ThreatDetector):
    """Detects unauthorized API access attempts."""
    
    async def detect(self, db: AsyncSession, logs: List[Any]) -> List[SecurityAlert]:
        alerts = []
        
        # Check for repeated API access denials
        api_denials = {}
        for log in logs:
            if log.action == "access_denied" and "api" in str(log.meta_data).lower():
                key = log.ip_address or "unknown"
                if key not in api_denials:
                    api_denials[key] = []
                api_denials[key].append(log)
        
        # Check for patterns suggesting API abuse
        for ip, denials in api_denials.items():
            if len(denials) >= 10:  # 10+ API denials in 5 minutes
                alerts.append(SecurityAlert(
                    id=f"api_{ip}_{datetime.utcnow().timestamp()}",
                    threat_type=ThreatType.UNAUTHORIZED_API_ACCESS,
                    severity=AlertSeverity.HIGH,
                    title="Unauthorized API Access Attempts",
                    description=f"Multiple unauthorized API access attempts from IP {ip}",
                    user_id=None,
                    workspace_id=None,
                    detected_at=datetime.utcnow(),
                    evidence=[{
                        "denial_count": len(denials),
                        "ip_address": ip,
                        "time_window": "5 minutes",
                        "api_endpoints": list(set(d.meta_data.get("endpoint", "unknown") for d in denials if d.meta_data))
                    }],
                    recommended_actions=[
                        "Block IP address",
                        "Review API security",
                        "Check for credential stuffing",
                        "Monitor for distributed attacks"
                    ]
                ))
        
        return alerts


# Global security monitor instance
security_monitor = SecurityMonitor()


async def run_security_monitoring():
    """Main security monitoring loop."""
    logger.info("Starting security monitoring service...")
    
    while True:
        try:
            alerts = await security_monitor.analyze_recent_activity()
            
            if alerts:
                logger.warning(f"Security monitoring detected {len(alerts)} new alerts")
                
                # Log alerts to audit system
                async with async_session_maker() as db:
                    for alert in alerts:
                        await create_audit_log(
                            db=db,
                            user_id=None,
                            action="security_alert_generated",
                            resource_type="security",
                            resource_id=alert.id,
                            meta_data={
                                "threat_type": alert.threat_type.value,
                                "severity": alert.severity.value,
                                "title": alert.title,
                                "affected_user": alert.user_id,
                                "evidence_count": len(alert.evidence)
                            },
                            risk_level="high"
                        )
            
            # Wait 5 minutes before next check
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Error in security monitoring: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry


# Function to start monitoring in background
def start_security_monitoring():
    """Start security monitoring as a background task."""
    asyncio.create_task(run_security_monitoring())