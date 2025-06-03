#!/usr/bin/env python3
"""
Quick Security Check for Web+ Backend

Performs essential security validations quickly.
"""
import os
import re
from pathlib import Path

def quick_security_audit():
    """Perform a quick security audit."""
    print("🔒 Running Quick Security Audit...")
    
    issues = []
    project_root = Path(".")
    
    # Check 1: CORS Configuration
    main_py = project_root / "main.py"
    if main_py.exists():
        content = main_py.read_text()
        if 'allow_origins=["*"]' in content:
            issues.append("⚠️  CORS allows all origins - should restrict in production")
        if 'SECRET_KEY' in content and 'SECRET_KEY' not in os.environ:
            issues.append("⚠️  Hardcoded SECRET_KEY found - should use environment variable")
    
    # Check 2: Environment Configuration
    env_file = project_root / ".env"
    gitignore = project_root / ".gitignore"
    if env_file.exists() and gitignore.exists():
        gitignore_content = gitignore.read_text()
        if ".env" not in gitignore_content:
            issues.append("🚨 CRITICAL: .env file not in .gitignore - secrets may be exposed")
    
    # Check 3: Password Security
    auth_files = list(project_root.glob("auth/*.py"))
    for auth_file in auth_files:
        content = auth_file.read_text()
        if "bcrypt" not in content and "password" in content.lower():
            issues.append(f"⚠️  {auth_file.name}: Not using bcrypt for password hashing")
    
    # Check 4: SQL Injection Protection
    py_files = list(project_root.glob("**/*.py"))
    for py_file in py_files:
        try:
            content = py_file.read_text()
            if re.search(r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE)', content, re.IGNORECASE):
                issues.append(f"🚨 CRITICAL: {py_file.name}: SQL injection risk with f-strings")
        except:
            continue
    
    # Check 5: Debug Mode
    for py_file in py_files:
        try:
            content = py_file.read_text()
            if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
                issues.append(f"⚠️  {py_file.name}: Debug mode enabled")
        except:
            continue
    
    # Results
    if not issues:
        print("✅ No critical security issues found!")
        print("🏎️  Security Status: READY TO RACE!")
        return True
    else:
        print(f"❌ Found {len(issues)} security issues:")
        for issue in issues:
            print(f"   {issue}")
        print("\n🔧 Fix these issues before racing!")
        return False

if __name__ == "__main__":
    quick_security_audit()