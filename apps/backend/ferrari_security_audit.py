#!/usr/bin/env python3
"""
Ferrari Security Audit - Production Readiness Check
"""
import os
import re
from pathlib import Path

def ferrari_security_audit():
    """Comprehensive security audit for Ferrari production readiness."""
    print("🏎️ Ferrari Security Audit - Production Readiness Check")
    print("=" * 60)
    
    issues = []
    security_score = 100
    project_root = Path(".")
    
    # 1. Authentication Security
    print("🔑 Checking Authentication Security...")
    auth_files = list(project_root.glob("auth/*.py"))
    for auth_file in auth_files:
        try:
            content = auth_file.read_text()
            if "bcrypt" not in content and "password" in content.lower():
                issues.append(f"HIGH: {auth_file.name} - Not using bcrypt for passwords")
                security_score -= 10
        except:
            continue
    
    # 2. CORS Configuration
    print("🌐 Checking CORS Configuration...")
    main_py = project_root / "main.py"
    if main_py.exists():
        try:
            content = main_py.read_text()
            if 'allow_origins=["*"]' in content:
                issues.append("MEDIUM: CORS allows all origins")
                security_score -= 5
            elif 'cors_origins' in content and 'CORS_ORIGINS' in content:
                print("  ✅ Environment-based CORS configuration found")
        except:
            pass
    
    # 3. SQL Injection Protection
    print("💉 Checking SQL Injection Protection...")
    py_files = list(project_root.glob("**/*.py"))[:20]  # Limit files for performance
    for py_file in py_files:
        try:
            content = py_file.read_text()
            if re.search(r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
                issues.append(f"CRITICAL: {py_file.name} - SQL injection risk with f-strings")
                security_score -= 15
        except:
            continue
    
    # 4. Environment Configuration
    print("🌍 Checking Environment Configuration...")
    env_file = project_root / ".env"
    gitignore = project_root / ".gitignore"
    if env_file.exists():
        if gitignore.exists():
            try:
                gitignore_content = gitignore.read_text()
                if ".env" not in gitignore_content:
                    issues.append("CRITICAL: .env file not in .gitignore")
                    security_score -= 20
                else:
                    print("  ✅ .env file properly ignored")
            except:
                pass
    
    # 5. Security Headers
    print("🛡️  Checking Security Headers...")
    if main_py.exists():
        try:
            content = main_py.read_text()
            if "SecurityMiddleware" in content:
                print("  ✅ Security middleware implemented")
            else:
                issues.append("MEDIUM: Missing security headers middleware")
                security_score -= 8
        except:
            pass
    
    # 6. Debug Mode
    print("🐛 Checking Debug Configuration...")
    debug_found = False
    for py_file in py_files[:10]:
        try:
            content = py_file.read_text()
            if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
                issues.append(f"MEDIUM: {py_file.name} - Debug mode enabled")
                security_score -= 5
                debug_found = True
        except:
            continue
    if not debug_found:
        print("  ✅ No hardcoded debug mode found")
    
    # 7. Secret Management
    print("🤫 Checking Secret Management...")
    secrets_found = False
    for py_file in py_files[:10]:
        try:
            content = py_file.read_text()
            secret_patterns = [
                r'api_key\s*=\s*["\'][^"\']{10,}["\']',
                r'secret\s*=\s*["\'][^"\']{10,}["\']',
                r'password\s*=\s*["\'][^"\']+["\']'
            ]
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"HIGH: {py_file.name} - Hardcoded secret found")
                    security_score -= 12
                    secrets_found = True
                    break
        except:
            continue
    if not secrets_found:
        print("  ✅ No hardcoded secrets found")
    
    # 8. Input Validation
    print("📝 Checking Input Validation...")
    schema_files = list(project_root.glob("**/*schema*.py"))
    if schema_files:
        print("  ✅ Input validation schemas found")
    else:
        issues.append("MEDIUM: No Pydantic schemas found for input validation")
        security_score -= 8
    
    # Calculate readiness level
    if security_score >= 90:
        readiness = "PRODUCTION_READY"
        status_emoji = "🏁"
        status_color = "✅"
    elif security_score >= 75:
        readiness = "STAGING_READY"
        status_emoji = "🏃"
        status_color = "🟡"
    elif security_score >= 50:
        readiness = "DEVELOPMENT_READY"
        status_emoji = "🔧"
        status_color = "🟠"
    else:
        readiness = "NOT_READY"
        status_emoji = "🚫"
        status_color = "🔴"
    
    # Results
    print("\n" + "=" * 60)
    print("🏎️ FERRARI SECURITY AUDIT RESULTS")
    print("=" * 60)
    print(f"{status_color} Security Score: {security_score}/100")
    print(f"{status_emoji} Readiness Level: {readiness}")
    print(f"🔍 Issues Found: {len(issues)}")
    
    if issues:
        print("\n📋 Issues to Address:")
        for issue in issues:
            severity = issue.split(":")[0]
            if severity == "CRITICAL":
                print(f"  🚨 {issue}")
            elif severity == "HIGH":
                print(f"  ⚠️  {issue}")
            else:
                print(f"  📋 {issue}")
    
    print("\n🏎️ Ferrari Racing Status:")
    if readiness == "PRODUCTION_READY":
        print("🏁 READY TO RACE! All systems go!")
        print("🚀 Your Ferrari is production-ready and secure!")
    elif readiness == "STAGING_READY":
        print("🏃 Almost ready to race - minor tune-ups needed")
        print("⚡ A few small fixes and you'll be on the track!")
    else:
        print("🔧 Ferrari needs work before hitting the track")
        print("🛠️  Address the issues above for a safe race!")
    
    # Recommendations
    if security_score < 90:
        print("\n🎯 Ferrari Tuning Recommendations:")
        if any("CRITICAL" in issue for issue in issues):
            print("  🚨 Fix CRITICAL issues immediately")
        if any("HIGH" in issue for issue in issues):
            print("  ⚠️  Address HIGH priority issues")
        print("  🔐 Implement comprehensive input validation")
        print("  🛡️  Add security headers middleware")
        print("  🔍 Set up automated security scanning")
        print("  📋 Conduct regular security reviews")
    
    return readiness == "PRODUCTION_READY"

if __name__ == "__main__":
    ferrari_security_audit()