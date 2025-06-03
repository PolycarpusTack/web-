#!/usr/bin/env python3
"""
Run comprehensive security audit for Web+ backend.
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    try:
        from security.security_audit import run_security_audit
        
        print("🏎️ Running Ferrari Security Audit...")
        print("=" * 50)
        
        project_root = Path(__file__).parent
        report = await run_security_audit(project_root)
        
        print("\n" + "=" * 50)
        print("🔒 SECURITY AUDIT COMPLETE")
        print("=" * 50)
        print(f"🎯 Security Score: {report['security_score']}/100")
        print(f"📊 Readiness Level: {report['readiness_level']}")
        print(f"🔍 Total Issues: {report['total_issues']}")
        
        if report['severity_breakdown']['CRITICAL'] > 0:
            print(f"🚨 CRITICAL Issues: {report['severity_breakdown']['CRITICAL']}")
        if report['severity_breakdown']['HIGH'] > 0:
            print(f"⚠️  HIGH Issues: {report['severity_breakdown']['HIGH']}")
        if report['severity_breakdown']['MEDIUM'] > 0:
            print(f"📋 MEDIUM Issues: {report['severity_breakdown']['MEDIUM']}")
        
        print("\n🏎️ Ferrari Racing Status:")
        if report['readiness_level'] == 'PRODUCTION_READY':
            print("✅ READY TO RACE! 🏁")
        elif report['readiness_level'] == 'STAGING_READY':
            print("🏃 Almost ready - minor fixes needed")
        else:
            print("🔧 Needs work before racing")
        
        print(f"\n📄 Full report saved to: security_report.json")
        
        return report['readiness_level'] == 'PRODUCTION_READY'
        
    except ImportError as e:
        print(f"⚠️  Could not import security audit module: {e}")
        print("Running basic security checks instead...")
        
        # Fall back to basic checks
        from simple_security_check import quick_security_check
        return quick_security_check()
    except Exception as e:
        print(f"❌ Security audit failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)