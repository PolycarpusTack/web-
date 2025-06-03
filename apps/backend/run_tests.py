#!/usr/bin/env python3
"""
Professional Test Runner for Web+ Backend

This script provides comprehensive testing capabilities with:
- Environment setup and validation
- Test discovery and execution
- Coverage reporting
- Performance benchmarking
- CI/CD integration
"""

import sys
import os
import subprocess
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

class TestRunner:
    """Professional test runner with comprehensive reporting and validation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.reports_dir = self.project_root / "test_reports"
        self.reports_dir.mkdir(exist_ok=True)
        self.start_time = time.time()
        
    def setup_environment(self) -> bool:
        """Set up the testing environment and validate dependencies."""
        print("🔧 Setting up test environment...")
        
        # Set environment variables for testing
        os.environ.update({
            "TESTING": "true",
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
            "SECRET_KEY": "test-secret-key-for-testing-only",
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "ENVIRONMENT": "test"
        })
        
        # Validate Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
            
        # Check if we're in the right directory
        if not (self.project_root / "main.py").exists():
            print("❌ Must run from backend directory")
            return False
            
        print("✅ Environment setup complete")
        return True
    
    def install_dependencies(self) -> bool:
        """Install or update testing dependencies."""
        print("📦 Checking dependencies...")
        
        try:
            # Install/upgrade testing dependencies
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True, capture_output=True)
            
            print("✅ Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def run_unit_tests(self, verbose: bool = False) -> Dict:
        """Run unit tests with coverage."""
        print("🧪 Running unit tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v" if verbose else "-q",
            "--tb=short",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=xml:test_reports/coverage.xml",
            "--cov-report=html:test_reports/htmlcov",
            "--junit-xml=test_reports/pytest-results.xml",
            "-m", "not slow and not integration",
            "--asyncio-mode=auto"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Tests timed out after 5 minutes",
                "returncode": -1
            }
    
    def run_integration_tests(self, verbose: bool = False) -> Dict:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v" if verbose else "-q",
            "--tb=short",
            "-m", "integration",
            "--asyncio-mode=auto"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Integration tests timed out after 10 minutes",
                "returncode": -1
            }
    
    def run_performance_tests(self) -> Dict:
        """Run performance and benchmarking tests."""
        print("⚡ Running performance tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "-m", "slow",
            "--benchmark-only",
            "--benchmark-json=test_reports/benchmark.json"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Performance tests timed out after 15 minutes",
                "returncode": -1
            }
    
    def run_security_tests(self) -> Dict:
        """Run security-focused tests."""
        print("🔒 Running security tests...")
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "-m", "security",
            "--tb=short"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Security tests timed out after 5 minutes",
                "returncode": -1
            }
    
    def check_code_quality(self) -> Dict:
        """Run code quality checks."""
        print("📊 Checking code quality...")
        
        results = {}
        
        # Run flake8 for style checking
        try:
            result = subprocess.run([
                sys.executable, "-m", "flake8", ".",
                "--max-line-length=100",
                "--exclude=migrations,venv,__pycache__",
                "--output-file=test_reports/flake8.txt"
            ], capture_output=True, text=True)
            
            results["flake8"] = {
                "success": result.returncode == 0,
                "issues": result.stdout.count("\n") if result.stdout else 0
            }
        except FileNotFoundError:
            results["flake8"] = {"success": True, "issues": 0, "note": "flake8 not installed"}
        
        # Run mypy for type checking
        try:
            result = subprocess.run([
                sys.executable, "-m", "mypy", ".",
                "--ignore-missing-imports",
                "--no-strict-optional"
            ], capture_output=True, text=True)
            
            results["mypy"] = {
                "success": result.returncode == 0,
                "issues": result.stdout.count("error:") if result.stdout else 0
            }
        except FileNotFoundError:
            results["mypy"] = {"success": True, "issues": 0, "note": "mypy not installed"}
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive test report."""
        total_time = time.time() - self.start_time
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration": round(total_time, 2),
            "results": results,
            "summary": {
                "total_tests": sum(1 for r in results.values() if isinstance(r, dict) and "success" in r),
                "passed": sum(1 for r in results.values() if isinstance(r, dict) and r.get("success", False)),
                "failed": sum(1 for r in results.values() if isinstance(r, dict) and not r.get("success", True))
            }
        }
        
        # Save JSON report
        with open(self.reports_dir / "test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate human-readable report
        report_text = f"""
📋 Web+ Backend Test Report
{'=' * 50}

🕐 Test Duration: {total_time:.2f} seconds
📅 Generated: {report['timestamp']}

📊 Summary:
✅ Passed: {report['summary']['passed']}
❌ Failed: {report['summary']['failed']}
📈 Total: {report['summary']['total_tests']}

📝 Detailed Results:
"""
        
        for test_type, result in results.items():
            if isinstance(result, dict) and "success" in result:
                status = "✅ PASSED" if result["success"] else "❌ FAILED"
                report_text += f"\n{test_type:.<20} {status}"
                
                if not result["success"] and result.get("stderr"):
                    report_text += f"\n   Error: {result['stderr'][:200]}..."
        
        # Save text report
        with open(self.reports_dir / "test_report.txt", "w") as f:
            f.write(report_text)
        
        return report_text
    
    def run_all(self, args) -> bool:
        """Run all tests and generate comprehensive report."""
        if not self.setup_environment():
            return False
        
        if args.install_deps:
            if not self.install_dependencies():
                return False
        
        results = {}
        
        # Run unit tests (always)
        results["unit_tests"] = self.run_unit_tests(args.verbose)
        
        # Run integration tests if requested
        if args.integration:
            results["integration_tests"] = self.run_integration_tests(args.verbose)
        
        # Run performance tests if requested
        if args.performance:
            results["performance_tests"] = self.run_performance_tests()
        
        # Run security tests if requested
        if args.security:
            results["security_tests"] = self.run_security_tests()
        
        # Check code quality if requested
        if args.quality:
            results["code_quality"] = self.check_code_quality()
        
        # Generate and display report
        report = self.generate_report(results)
        print(report)
        
        # Return success if all tests passed
        all_passed = all(
            result.get("success", True) 
            for result in results.values() 
            if isinstance(result, dict) and "success" in result
        )
        
        if all_passed:
            print("\n🎉 All tests passed! Ready to race! 🏎️")
        else:
            print("\n🚨 Some tests failed. Check the reports for details.")
        
        return all_passed


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Web+ Backend Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--integration", "-i", action="store_true", help="Run integration tests")
    parser.add_argument("--performance", "-p", action="store_true", help="Run performance tests")
    parser.add_argument("--security", "-s", action="store_true", help="Run security tests")
    parser.add_argument("--quality", "-q", action="store_true", help="Run code quality checks")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies first")
    parser.add_argument("--all", "-a", action="store_true", help="Run all test types")
    
    args = parser.parse_args()
    
    # If --all is specified, enable all test types
    if args.all:
        args.integration = True
        args.performance = True
        args.security = True
        args.quality = True
    
    runner = TestRunner()
    success = runner.run_all(args)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()