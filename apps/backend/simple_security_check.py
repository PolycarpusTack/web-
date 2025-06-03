#!/usr/bin/env python3
"""
Simple Security Check for Web+ Backend
Fast security validation without external dependencies.
"""
import os
import re
from pathlib import Path

def quick_security_check():
    """Perform a fast security check."""
    print("🔒 Running Fast Security Check...")
    
    issues = []
    project_root = Path(".")
    
    # Check 1: CORS Configuration
    main_py = project_root / "main.py"
    if main_py.exists():
        try:
            content = main_py.read_text()
            if 'allow_origins=["*"]' in content:
                issues.append("⚠️  CORS allows all origins - restrict in production")
        except Exception as e:
            print(f"Could not read main.py: {e}")
    
    # Check 2: Environment Configuration
    env_file = project_root / ".env"
    gitignore = project_root / ".gitignore"
    if env_file.exists() and gitignore.exists():
        try:
            gitignore_content = gitignore.read_text()
            if ".env" not in gitignore_content:
                issues.append("🚨 CRITICAL: .env file not in .gitignore")
        except Exception as e:
            print(f"Could not read .gitignore: {e}")
    
    # Check 3: Debug Mode
    try:
        py_files = list(project_root.glob("*.py"))[:10]  # Limit to first 10 files
        for py_file in py_files:
            try:
                content = py_file.read_text()
                if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
                    issues.append(f"⚠️  {py_file.name}: Debug mode enabled")
            except:
                continue
    except Exception as e:
        print(f"Could not scan Python files: {e}")
    
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
    quick_security_check()