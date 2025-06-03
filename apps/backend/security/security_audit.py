"""
Comprehensive Security Audit and Hardening for Web+ Backend

This module provides automated security checks and hardening measures
to ensure our Ferrari is bulletproof before racing.
"""
import os
import re
import json
import asyncio
import hashlib
import secrets
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from passlib.context import CryptContext
import jwt


class SeverityLevel(Enum):
    """Security issue severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityIssue:
    """Represents a security issue found during audit."""
    title: str
    description: str
    severity: SeverityLevel
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    cve_reference: Optional[str] = None


class SecurityAuditor:
    """Comprehensive security auditor for Web+ backend."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[SecurityIssue] = []
        self.report_data = {}
        
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run a comprehensive security audit."""
        print("🔒 Starting comprehensive security audit...")
        
        # Authentication and Authorization Checks
        await self._audit_authentication()
        await self._audit_authorization()
        
        # Input Validation and Sanitization
        await self._audit_input_validation()
        await self._audit_sql_injection_protection()
        
        # Cryptography and Secrets Management
        await self._audit_password_security()
        await self._audit_jwt_security()
        await self._audit_secrets_management()
        
        # Network Security
        await self._audit_cors_configuration()
        await self._audit_https_configuration()
        
        # Data Protection
        await self._audit_data_exposure()
        await self._audit_logging_security()
        
        # Dependency Security
        await self._audit_dependencies()
        
        # Infrastructure Security
        await self._audit_file_permissions()
        await self._audit_environment_configuration()
        
        # Generate comprehensive report
        return await self._generate_security_report()
    
    async def _audit_authentication(self):
        """Audit authentication mechanisms."""
        print("  🔑 Auditing authentication...")
        
        # Check for proper password hashing
        auth_files = list(self.project_root.glob("auth/*.py"))
        for file_path in auth_files:
            content = await self._read_file(file_path)
            
            # Check for weak password requirements
            if "password" in content.lower():
                if not re.search(r'len\([^)]+\)\s*>=?\s*[8-9]', content):
                    self.issues.append(SecurityIssue(
                        title="Weak Password Requirements",
                        description="Password minimum length should be at least 8 characters",
                        severity=SeverityLevel.MEDIUM,
                        file_path=str(file_path),
                        recommendation="Implement minimum password length of 8+ characters"
                    ))
            
            # Check for proper bcrypt usage
            if "bcrypt" not in content and "password" in content:
                self.issues.append(SecurityIssue(
                    title="Weak Password Hashing",
                    description="Not using bcrypt for password hashing",
                    severity=SeverityLevel.HIGH,
                    file_path=str(file_path),
                    recommendation="Use bcrypt with proper cost factor (12+)"
                ))
    
    async def _audit_authorization(self):
        """Audit authorization and access control."""
        print("  🛡️ Auditing authorization...")
        
        # Check for proper role-based access control
        router_files = list(self.project_root.glob("**/*router*.py")) + list(self.project_root.glob("**/main.py"))
        
        for file_path in router_files:
            content = await self._read_file(file_path)
            
            # Check for endpoints without authentication
            endpoints = re.findall(r'@[^.]+\.(get|post|put|delete|patch)\([^)]*\)', content)
            if endpoints:
                # Check if there are authentication dependencies
                if "Depends(" not in content or "get_current_user" not in content:
                    self.issues.append(SecurityIssue(
                        title="Unauthenticated Endpoints",
                        description="Endpoints found without authentication checks",
                        severity=SeverityLevel.HIGH,
                        file_path=str(file_path),
                        recommendation="Add authentication dependencies to all sensitive endpoints"
                    ))
    
    async def _audit_input_validation(self):
        """Audit input validation and sanitization."""
        print("  📝 Auditing input validation...")
        
        # Check for proper input validation using Pydantic
        schema_files = list(self.project_root.glob("**/*schema*.py"))
        
        if not schema_files:
            self.issues.append(SecurityIssue(
                title="Missing Input Validation Schemas",
                description="No Pydantic schemas found for input validation",
                severity=SeverityLevel.HIGH,
                recommendation="Implement Pydantic schemas for all API endpoints"
            ))
        
        # Check for dangerous eval() or exec() usage
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            content = await self._read_file(file_path)
            
            if re.search(r'\beval\s*\(', content):
                self.issues.append(SecurityIssue(
                    title="Dangerous eval() Usage",
                    description="Found eval() function which can execute arbitrary code",
                    severity=SeverityLevel.CRITICAL,
                    file_path=str(file_path),
                    recommendation="Replace eval() with safe alternatives like ast.literal_eval()"
                ))
            
            if re.search(r'\bexec\s*\(', content):
                # Check if it's in pipeline code (which might be intentional)
                if "pipeline" not in str(file_path).lower():
                    self.issues.append(SecurityIssue(
                        title="Dangerous exec() Usage",
                        description="Found exec() function which can execute arbitrary code",
                        severity=SeverityLevel.HIGH,
                        file_path=str(file_path),
                        recommendation="Ensure exec() is properly sandboxed and validated"
                    ))
    
    async def _audit_sql_injection_protection(self):
        """Audit SQL injection protection."""
        print("  💉 Auditing SQL injection protection...")
        
        # Check for raw SQL queries
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            content = await self._read_file(file_path)
            
            # Look for string formatting in SQL queries
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*[%{}].*format\(', content, re.IGNORECASE):
                self.issues.append(SecurityIssue(
                    title="Potential SQL Injection",
                    description="Found string formatting in SQL queries",
                    severity=SeverityLevel.CRITICAL,
                    file_path=str(file_path),
                    recommendation="Use parameterized queries with SQLAlchemy ORM"
                ))
            
            # Check for f-strings in SQL
            if re.search(r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
                self.issues.append(SecurityIssue(
                    title="SQL Injection via F-strings",
                    description="Found f-strings in SQL queries",
                    severity=SeverityLevel.HIGH,
                    file_path=str(file_path),
                    recommendation="Use parameterized queries instead of f-strings"
                ))
    
    async def _audit_password_security(self):
        """Audit password security practices."""
        print("  🔐 Auditing password security...")
        
        # Check password storage and handling
        auth_files = list(self.project_root.glob("auth/*.py"))
        for file_path in auth_files:
            content = await self._read_file(file_path)
            
            # Check for hardcoded passwords
            if re.search(r'password\s*=\s*["\'][^"\']+["\']', content):
                self.issues.append(SecurityIssue(
                    title="Hardcoded Password",
                    description="Found hardcoded password in source code",
                    severity=SeverityLevel.CRITICAL,
                    file_path=str(file_path),
                    recommendation="Move passwords to environment variables"
                ))
            
            # Check bcrypt cost factor
            bcrypt_match = re.search(r'rounds=(\d+)', content)
            if bcrypt_match:
                rounds = int(bcrypt_match.group(1))
                if rounds < 12:
                    self.issues.append(SecurityIssue(
                        title="Weak bcrypt Cost Factor",
                        description=f"bcrypt rounds set to {rounds}, should be at least 12",
                        severity=SeverityLevel.MEDIUM,
                        file_path=str(file_path),
                        recommendation="Increase bcrypt rounds to at least 12"
                    ))
    
    async def _audit_jwt_security(self):
        """Audit JWT token security."""
        print("  🎫 Auditing JWT security...")
        
        jwt_files = list(self.project_root.glob("auth/*jwt*.py"))
        for file_path in jwt_files:
            content = await self._read_file(file_path)
            
            # Check for weak JWT secrets
            if re.search(r'SECRET_KEY\s*=\s*["\'][^"\']{1,20}["\']', content):
                self.issues.append(SecurityIssue(
                    title="Weak JWT Secret",
                    description="JWT secret key appears to be too short",
                    severity=SeverityLevel.HIGH,
                    file_path=str(file_path),
                    recommendation="Use a strong, randomly generated secret key (32+ characters)"
                ))
            
            # Check token expiration
            if "ACCESS_TOKEN_EXPIRE" not in content:
                self.issues.append(SecurityIssue(
                    title="Missing Token Expiration",
                    description="No token expiration configuration found",
                    severity=SeverityLevel.MEDIUM,
                    file_path=str(file_path),
                    recommendation="Implement proper token expiration (15-30 minutes)"
                ))
    
    async def _audit_secrets_management(self):
        """Audit secrets and environment variable management."""
        print("  🤫 Auditing secrets management...")
        
        # Check for hardcoded secrets
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            content = await self._read_file(file_path)
            
            # Look for common secret patterns
            secret_patterns = [
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'password\s*=\s*["\'][^"\']+["\']'
            ]
            
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.issues.append(SecurityIssue(
                        title="Hardcoded Secret",
                        description="Found hardcoded secret in source code",
                        severity=SeverityLevel.HIGH,
                        file_path=str(file_path),
                        recommendation="Move secrets to environment variables or secure vault"
                    ))
        
        # Check for .env file exposure
        env_file = self.project_root / ".env"
        if env_file.exists():
            # Check if .env is in .gitignore
            gitignore = self.project_root / ".gitignore"
            if gitignore.exists():
                gitignore_content = await self._read_file(gitignore)
                if ".env" not in gitignore_content:
                    self.issues.append(SecurityIssue(
                        title="Environment File Not Ignored",
                        description=".env file exists but not in .gitignore",
                        severity=SeverityLevel.HIGH,
                        file_path=str(gitignore),
                        recommendation="Add .env to .gitignore to prevent secret exposure"
                    ))
    
    async def _audit_cors_configuration(self):
        """Audit CORS configuration."""
        print("  🌐 Auditing CORS configuration...")
        
        main_file = self.project_root / "main.py"
        if main_file.exists():
            content = await self._read_file(main_file)
            
            # Check for overly permissive CORS
            if 'allow_origins=["*"]' in content:
                self.issues.append(SecurityIssue(
                    title="Overly Permissive CORS",
                    description="CORS allows all origins (*)",
                    severity=SeverityLevel.MEDIUM,
                    file_path=str(main_file),
                    recommendation="Restrict CORS to specific trusted domains in production"
                ))
            
            if 'allow_credentials=True' in content and 'allow_origins=["*"]' in content:
                self.issues.append(SecurityIssue(
                    title="Dangerous CORS Configuration",
                    description="CORS allows credentials with wildcard origins",
                    severity=SeverityLevel.HIGH,
                    file_path=str(main_file),
                    recommendation="Never use allow_credentials=True with allow_origins=['*']"
                ))
    
    async def _audit_https_configuration(self):
        """Audit HTTPS and TLS configuration."""
        print("  🔒 Auditing HTTPS configuration...")
        
        # Check for security headers
        main_file = self.project_root / "main.py"
        if main_file.exists():
            content = await self._read_file(main_file)
            
            security_headers = [
                "Strict-Transport-Security",
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Content-Security-Policy"
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in content:
                    missing_headers.append(header)
            
            if missing_headers:
                self.issues.append(SecurityIssue(
                    title="Missing Security Headers",
                    description=f"Missing security headers: {', '.join(missing_headers)}",
                    severity=SeverityLevel.MEDIUM,
                    file_path=str(main_file),
                    recommendation="Implement security headers middleware"
                ))
    
    async def _audit_data_exposure(self):
        """Audit for potential data exposure."""
        print("  📊 Auditing data exposure...")
        
        # Check for password fields in API responses
        router_files = list(self.project_root.glob("**/*router*.py"))
        for file_path in router_files:
            content = await self._read_file(file_path)
            
            # Look for password fields being returned
            if re.search(r'password.*return', content, re.IGNORECASE | re.DOTALL):
                self.issues.append(SecurityIssue(
                    title="Password Field Exposure",
                    description="Password field might be exposed in API response",
                    severity=SeverityLevel.HIGH,
                    file_path=str(file_path),
                    recommendation="Exclude password fields from API responses"
                ))
    
    async def _audit_logging_security(self):
        """Audit logging for security issues."""
        print("  📝 Auditing logging security...")
        
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            content = await self._read_file(file_path)
            
            # Check for logging sensitive information
            if re.search(r'log.*password', content, re.IGNORECASE):
                self.issues.append(SecurityIssue(
                    title="Sensitive Data in Logs",
                    description="Password might be logged",
                    severity=SeverityLevel.HIGH,
                    file_path=str(file_path),
                    recommendation="Never log sensitive information like passwords"
                ))
    
    async def _audit_dependencies(self):
        """Audit dependencies for known vulnerabilities."""
        print("  📦 Auditing dependencies...")
        
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            content = await self._read_file(requirements_file)
            
            # Check for unpinned dependencies
            unpinned = re.findall(r'^([^>=<!\n]+)$', content, re.MULTILINE)
            if unpinned:
                self.issues.append(SecurityIssue(
                    title="Unpinned Dependencies",
                    description=f"Unpinned dependencies found: {', '.join(unpinned[:5])}",
                    severity=SeverityLevel.MEDIUM,
                    file_path=str(requirements_file),
                    recommendation="Pin all dependencies to specific versions"
                ))
    
    async def _audit_file_permissions(self):
        """Audit file permissions."""
        print("  📁 Auditing file permissions...")
        
        # Check for overly permissive files
        sensitive_files = [".env", "config.py", "main.py", "requirements.txt"]
        
        for filename in sensitive_files:
            file_path = self.project_root / filename
            if file_path.exists():
                try:
                    # Check file permissions (Unix-like systems)
                    stat_info = file_path.stat()
                    permissions = oct(stat_info.st_mode)[-3:]
                    
                    if permissions > "644":
                        self.issues.append(SecurityIssue(
                            title="Overly Permissive File Permissions",
                            description=f"{filename} has permissions {permissions}",
                            severity=SeverityLevel.LOW,
                            file_path=str(file_path),
                            recommendation="Set file permissions to 644 or more restrictive"
                        ))
                except Exception:
                    # Skip permission check on systems that don't support it
                    pass
    
    async def _audit_environment_configuration(self):
        """Audit environment configuration."""
        print("  🌍 Auditing environment configuration...")
        
        # Check for debug mode in production indicators
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            content = await self._read_file(file_path)
            
            if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
                self.issues.append(SecurityIssue(
                    title="Debug Mode Enabled",
                    description="Debug mode found enabled",
                    severity=SeverityLevel.MEDIUM,
                    file_path=str(file_path),
                    recommendation="Disable debug mode in production"
                ))
    
    async def _read_file(self, file_path: Path) -> str:
        """Safely read file content."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception:
            return ""
    
    async def _generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        print("📋 Generating security report...")
        
        # Categorize issues by severity
        severity_counts = {level.value: 0 for level in SeverityLevel}
        for issue in self.issues:
            severity_counts[issue.severity.value] += 1
        
        # Calculate security score (0-100)
        total_issues = len(self.issues)
        critical_weight = severity_counts["CRITICAL"] * 10
        high_weight = severity_counts["HIGH"] * 5
        medium_weight = severity_counts["MEDIUM"] * 2
        low_weight = severity_counts["LOW"] * 1
        
        weighted_score = critical_weight + high_weight + medium_weight + low_weight
        max_score = 100
        security_score = max(0, max_score - weighted_score)
        
        # Determine readiness level
        if security_score >= 90:
            readiness = "PRODUCTION_READY"
        elif security_score >= 75:
            readiness = "STAGING_READY"
        elif security_score >= 50:
            readiness = "DEVELOPMENT_READY"
        else:
            readiness = "NOT_READY"
        
        report = {
            "security_score": security_score,
            "readiness_level": readiness,
            "total_issues": total_issues,
            "severity_breakdown": severity_counts,
            "issues": [
                {
                    "title": issue.title,
                    "description": issue.description,
                    "severity": issue.severity.value,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "recommendation": issue.recommendation,
                    "cve_reference": issue.cve_reference
                }
                for issue in self.issues
            ],
            "recommendations": self._generate_recommendations()
        }
        
        # Save report
        report_file = self.project_root / "security_report.json"
        async with aiofiles.open(report_file, 'w') as f:
            await f.write(json.dumps(report, indent=2))
        
        print(f"📊 Security Score: {security_score}/100")
        print(f"🎯 Readiness Level: {readiness}")
        print(f"🔍 Issues Found: {total_issues}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate prioritized security recommendations."""
        recommendations = []
        
        # Critical issues first
        critical_issues = [i for i in self.issues if i.severity == SeverityLevel.CRITICAL]
        if critical_issues:
            recommendations.append("🚨 IMMEDIATE: Fix all CRITICAL security issues before deployment")
        
        # High priority issues
        high_issues = [i for i in self.issues if i.severity == SeverityLevel.HIGH]
        if high_issues:
            recommendations.append("⚠️ HIGH PRIORITY: Address HIGH severity issues within 24 hours")
        
        # General recommendations
        recommendations.extend([
            "🔐 Implement comprehensive input validation on all endpoints",
            "🔑 Use strong, randomly generated secrets for all cryptographic operations",
            "🛡️ Add security headers middleware for all HTTP responses",
            "📊 Implement proper error handling without information disclosure",
            "🔍 Set up automated security scanning in CI/CD pipeline",
            "📋 Conduct regular security audits and penetration testing",
            "🎯 Implement proper logging and monitoring for security events"
        ])
        
        return recommendations


async def run_security_audit(project_root: Path = None) -> Dict[str, Any]:
    """Run a comprehensive security audit."""
    if project_root is None:
        project_root = Path(__file__).parent.parent
    
    auditor = SecurityAuditor(project_root)
    return await auditor.run_full_audit()


if __name__ == "__main__":
    asyncio.run(run_security_audit())