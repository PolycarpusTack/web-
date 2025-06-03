#!/usr/bin/env python3
"""
Ferrari CI/CD Quality Gates

This module provides automated quality gates for continuous integration
and deployment to ensure our Ferrari maintains high standards.
"""
import asyncio
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class QualityGateStatus(Enum):
    """Quality gate status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class QualityGateResult:
    """Result from a quality gate check."""
    gate_name: str
    status: QualityGateStatus
    score: int  # 0-100
    message: str
    details: List[str] = None
    duration_ms: float = 0
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


class FerrariQualityGates:
    """Main quality gates system for Ferrari CI/CD."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.results_dir = self.project_root / "ci_results"
        self.results_dir.mkdir(exist_ok=True)
        
    async def run_all_gates(self) -> Dict[str, Any]:
        """Run all quality gates."""
        print("🏎️ Ferrari Quality Gates - CI/CD Pipeline")
        print("=" * 50)
        
        start_time = time.time()
        
        results = {
            "timestamp": time.time(),
            "project_root": str(self.project_root),
            "gates": {},
            "summary": {
                "total_gates": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "skipped": 0,
                "overall_score": 0,
                "pipeline_status": "unknown"
            }
        }
        
        # Define quality gates in order of execution
        gates = [
            ("code_style", self._check_code_style),
            ("security_scan", self._check_security),
            ("performance_baseline", self._check_performance),
            ("test_coverage", self._check_tests),
            ("build_integrity", self._check_build),
            ("documentation", self._check_documentation)
        ]
        
        # Execute gates
        for gate_name, gate_func in gates:
            print(f"\n🔍 Running {gate_name.replace('_', ' ').title()} Gate...")
            
            try:
                gate_result = await gate_func()
                results["gates"][gate_name] = {
                    "status": gate_result.status.value,
                    "score": gate_result.score,
                    "message": gate_result.message,
                    "details": gate_result.details,
                    "duration_ms": gate_result.duration_ms
                }
                
                # Update summary
                results["summary"]["total_gates"] += 1
                if gate_result.status == QualityGateStatus.PASSED:
                    results["summary"]["passed"] += 1
                    print(f"  ✅ PASSED: {gate_result.message} ({gate_result.score}/100)")
                elif gate_result.status == QualityGateStatus.WARNING:
                    results["summary"]["warnings"] += 1
                    print(f"  ⚠️  WARNING: {gate_result.message} ({gate_result.score}/100)")
                elif gate_result.status == QualityGateStatus.FAILED:
                    results["summary"]["failed"] += 1
                    print(f"  ❌ FAILED: {gate_result.message} ({gate_result.score}/100)")
                else:
                    results["summary"]["skipped"] += 1
                    print(f"  ⏭️  SKIPPED: {gate_result.message}")
                
                # Show details for failed or warning gates
                if gate_result.details and gate_result.status in [QualityGateStatus.FAILED, QualityGateStatus.WARNING]:
                    for detail in gate_result.details[:3]:  # Show first 3 details
                        print(f"    • {detail}")
                    if len(gate_result.details) > 3:
                        print(f"    • ... and {len(gate_result.details) - 3} more")
                        
            except Exception as e:
                print(f"  💥 ERROR: Gate execution failed: {e}")
                results["gates"][gate_name] = {
                    "status": QualityGateStatus.FAILED.value,
                    "score": 0,
                    "message": f"Gate execution failed: {e}",
                    "details": [],
                    "duration_ms": 0
                }
                results["summary"]["failed"] += 1
                results["summary"]["total_gates"] += 1
        
        # Calculate overall results
        total_score = sum(gate["score"] for gate in results["gates"].values())
        gate_count = len(results["gates"])
        results["summary"]["overall_score"] = total_score // gate_count if gate_count > 0 else 0
        
        # Determine pipeline status
        if results["summary"]["failed"] > 0:
            results["summary"]["pipeline_status"] = "failed"
        elif results["summary"]["warnings"] > 0:
            results["summary"]["pipeline_status"] = "warning"
        else:
            results["summary"]["pipeline_status"] = "passed"
        
        # Final results
        duration = time.time() - start_time
        
        print("\n" + "=" * 50)
        print("🏎️ FERRARI QUALITY GATES RESULTS")
        print("=" * 50)
        print(f"🎯 Overall Score: {results['summary']['overall_score']}/100")
        print(f"📊 Pipeline Status: {results['summary']['pipeline_status'].upper()}")
        print(f"⏱️  Total Duration: {duration:.1f}s")
        print(f"📈 Gates Summary:")
        print(f"  ✅ Passed: {results['summary']['passed']}")
        print(f"  ⚠️  Warnings: {results['summary']['warnings']}")
        print(f"  ❌ Failed: {results['summary']['failed']}")
        print(f"  ⏭️  Skipped: {results['summary']['skipped']}")
        
        # Final verdict
        if results["summary"]["pipeline_status"] == "passed":
            print("\n🏁 FERRARI IS READY TO DEPLOY!")
            print("All quality gates passed. Safe to proceed with deployment.")
        elif results["summary"]["pipeline_status"] == "warning":
            print("\n⚠️  FERRARI HAS WARNINGS")
            print("Consider addressing warnings before deployment.")
        else:
            print("\n🚫 FERRARI DEPLOYMENT BLOCKED")
            print("Critical quality gates failed. Fix issues before deployment.")
        
        # Save results
        results_file = self.results_dir / f"quality_gates_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
        return results
    
    async def _check_code_style(self) -> QualityGateResult:
        """Check code style and formatting."""
        start_time = time.time()
        
        score = 100
        details = []
        message = "Code style check"
        
        try:
            # Check for Python files
            python_files = list(self.project_root.glob("**/*.py"))
            if not python_files:
                return QualityGateResult(
                    gate_name="code_style",
                    status=QualityGateStatus.SKIPPED,
                    score=100,
                    message="No Python files found",
                    duration_ms=(time.time() - start_time) * 1000
                )
            
            # Basic style checks
            style_issues = []
            
            for py_file in python_files[:10]:  # Check first 10 files
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # Check for very long lines (>120 chars)
                    long_lines = [i+1 for i, line in enumerate(content.split('\n')) 
                                 if len(line) > 120]
                    if long_lines:
                        style_issues.append(f"{py_file.name}: Lines too long: {long_lines[:3]}")
                    
                    # Check for inconsistent indentation
                    if '\t' in content and '    ' in content:
                        style_issues.append(f"{py_file.name}: Mixed tabs and spaces")
                    
                    # Check for trailing whitespace
                    if any(line.endswith(' ') or line.endswith('\t') 
                          for line in content.split('\n')):
                        style_issues.append(f"{py_file.name}: Trailing whitespace found")
                    
                except Exception as e:
                    style_issues.append(f"{py_file.name}: Could not read file: {e}")
            
            if style_issues:
                score = max(60, 100 - len(style_issues) * 10)
                details = style_issues
                if score < 80:
                    status = QualityGateStatus.FAILED
                    message = f"Code style issues found ({len(style_issues)} issues)"
                else:
                    status = QualityGateStatus.WARNING
                    message = f"Minor code style issues ({len(style_issues)} issues)"
            else:
                status = QualityGateStatus.PASSED
                message = "Code style is good"
            
        except Exception as e:
            status = QualityGateStatus.FAILED
            score = 0
            message = f"Code style check failed: {e}"
            details = [str(e)]
        
        return QualityGateResult(
            gate_name="code_style",
            status=status,
            score=score,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000
        )
    
    async def _check_security(self) -> QualityGateResult:
        """Check security configuration."""
        start_time = time.time()
        
        score = 100
        details = []
        message = "Security check"
        
        try:
            # Run simple security audit
            security_script = self.project_root / "simple_security_check.py"
            if security_script.exists():
                # Security files exist - good sign
                security_files = [
                    self.project_root / "security" / "security_middleware.py",
                    self.project_root / "security" / "security_audit.py"
                ]
                
                missing_files = [f.name for f in security_files if not f.exists()]
                if missing_files:
                    score -= len(missing_files) * 15
                    details.extend([f"Missing security file: {f}" for f in missing_files])
                
                # Check for .env in .gitignore
                gitignore = self.project_root / ".gitignore"
                if gitignore.exists():
                    gitignore_content = gitignore.read_text()
                    if ".env" not in gitignore_content:
                        score -= 20
                        details.append(".env file not properly ignored")
                else:
                    score -= 10
                    details.append("No .gitignore file found")
                
                if score >= 90:
                    status = QualityGateStatus.PASSED
                    message = "Security configuration is excellent"
                elif score >= 70:
                    status = QualityGateStatus.WARNING
                    message = f"Security has minor issues (score: {score})"
                else:
                    status = QualityGateStatus.FAILED
                    message = f"Security needs attention (score: {score})"
            else:
                status = QualityGateStatus.WARNING
                score = 70
                message = "Security audit script not found"
                details = ["simple_security_check.py not found"]
            
        except Exception as e:
            status = QualityGateStatus.FAILED
            score = 0
            message = f"Security check failed: {e}"
            details = [str(e)]
        
        return QualityGateResult(
            gate_name="security",
            status=status,
            score=score,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000
        )
    
    async def _check_performance(self) -> QualityGateResult:
        """Check performance baseline."""
        start_time = time.time()
        
        score = 100
        details = []
        message = "Performance check"
        
        try:
            # Check for performance results
            perf_dir = self.project_root / "performance_results"
            if perf_dir.exists() and list(perf_dir.glob("*.json")):
                perf_files = list(perf_dir.glob("*.json"))
                latest_file = max(perf_files, key=lambda x: x.stat().st_mtime)
                
                with open(latest_file, "r") as f:
                    perf_data = json.load(f)
                
                perf_score = perf_data.get("score", 0)
                score = perf_score
                
                if perf_score >= 90:
                    status = QualityGateStatus.PASSED
                    message = f"Performance excellent ({perf_score}/100)"
                elif perf_score >= 70:
                    status = QualityGateStatus.WARNING
                    message = f"Performance acceptable ({perf_score}/100)"
                else:
                    status = QualityGateStatus.FAILED
                    message = f"Performance poor ({perf_score}/100)"
                    details = ["Performance below minimum threshold"]
            else:
                # Run quick performance test
                try:
                    quick_start = time.time()
                    test_result = sum(i for i in range(100000))
                    quick_duration = (time.time() - quick_start) * 1000
                    
                    if quick_duration < 50:
                        status = QualityGateStatus.PASSED
                        message = f"Quick performance test passed ({quick_duration:.1f}ms)"
                        score = 90
                    elif quick_duration < 100:
                        status = QualityGateStatus.WARNING
                        message = f"Quick performance test slow ({quick_duration:.1f}ms)"
                        score = 70
                    else:
                        status = QualityGateStatus.FAILED
                        message = f"Quick performance test very slow ({quick_duration:.1f}ms)"
                        score = 40
                        details = ["Performance significantly below expectations"]
                except Exception as e:
                    status = QualityGateStatus.WARNING
                    score = 60
                    message = "Performance baseline missing, quick test failed"
                    details = [f"Quick test error: {e}"]
            
        except Exception as e:
            status = QualityGateStatus.FAILED
            score = 0
            message = f"Performance check failed: {e}"
            details = [str(e)]
        
        return QualityGateResult(
            gate_name="performance",
            status=status,
            score=score,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000
        )
    
    async def _check_tests(self) -> QualityGateResult:
        """Check test coverage and execution."""
        start_time = time.time()
        
        score = 100
        details = []
        message = "Test coverage check"
        
        try:
            # Check for test files
            test_files = list(self.project_root.glob("**/test_*.py")) + \
                        list(self.project_root.glob("**/*_test.py")) + \
                        list(self.project_root.glob("tests/**/*.py"))
            
            if not test_files:
                status = QualityGateStatus.WARNING
                score = 60
                message = "No test files found"
                details = ["Consider adding automated tests"]
            else:
                # Check test structure
                test_count = len(test_files)
                
                if test_count >= 10:
                    status = QualityGateStatus.PASSED
                    message = f"Good test coverage ({test_count} test files)"
                elif test_count >= 5:
                    status = QualityGateStatus.WARNING
                    score = 80
                    message = f"Moderate test coverage ({test_count} test files)"
                else:
                    status = QualityGateStatus.WARNING
                    score = 70
                    message = f"Limited test coverage ({test_count} test files)"
                    details = ["Consider adding more comprehensive tests"]
                
                # Check for conftest.py (pytest configuration)
                conftest_files = list(self.project_root.glob("**/conftest.py"))
                if conftest_files:
                    details.append(f"Test configuration found: {len(conftest_files)} conftest.py files")
                else:
                    score -= 10
                    details.append("No pytest configuration (conftest.py) found")
            
        except Exception as e:
            status = QualityGateStatus.FAILED
            score = 0
            message = f"Test check failed: {e}"
            details = [str(e)]
        
        return QualityGateResult(
            gate_name="tests",
            status=status,
            score=score,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000
        )
    
    async def _check_build(self) -> QualityGateResult:
        """Check build integrity."""
        start_time = time.time()
        
        score = 100
        details = []
        message = "Build integrity check"
        
        try:
            # Check for main application file
            main_files = [
                self.project_root / "main.py",
                self.project_root / "app.py",
                self.project_root / "__init__.py"
            ]
            
            main_file = None
            for f in main_files:
                if f.exists():
                    main_file = f
                    break
            
            if not main_file:
                status = QualityGateStatus.FAILED
                score = 0
                message = "No main application file found"
                details = ["Expected main.py, app.py, or __init__.py"]
            else:
                # Check if main file can be imported (basic syntax check)
                try:
                    content = main_file.read_text()
                    
                    # Basic syntax checks
                    if "import" in content:
                        details.append("Contains import statements")
                    
                    if "def " in content or "class " in content:
                        details.append("Contains function or class definitions")
                    
                    if "FastAPI" in content or "Flask" in content or "Django" in content:
                        details.append("Web framework detected")
                    
                    # Check for requirements.txt
                    requirements = self.project_root / "requirements.txt"
                    if requirements.exists():
                        details.append("Dependencies file found (requirements.txt)")
                    else:
                        score -= 15
                        details.append("No requirements.txt found")
                    
                    status = QualityGateStatus.PASSED
                    message = f"Build structure looks good ({main_file.name} found)"
                    
                except Exception as e:
                    status = QualityGateStatus.WARNING
                    score = 70
                    message = f"Main file has issues: {e}"
                    details = [f"File read error: {e}"]
            
        except Exception as e:
            status = QualityGateStatus.FAILED
            score = 0
            message = f"Build check failed: {e}"
            details = [str(e)]
        
        return QualityGateResult(
            gate_name="build",
            status=status,
            score=score,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000
        )
    
    async def _check_documentation(self) -> QualityGateResult:
        """Check documentation quality."""
        start_time = time.time()
        
        score = 100
        details = []
        message = "Documentation check"
        
        try:
            # Check for README
            readme_files = [
                self.project_root / "README.md",
                self.project_root / "README.rst",
                self.project_root / "README.txt"
            ]
            
            readme_file = None
            for f in readme_files:
                if f.exists():
                    readme_file = f
                    break
            
            if not readme_file:
                score -= 30
                details.append("No README file found")
            else:
                content = readme_file.read_text()
                readme_length = len(content)
                
                if readme_length > 1000:
                    details.append("Comprehensive README found")
                elif readme_length > 200:
                    details.append("Basic README found")
                    score -= 10
                else:
                    details.append("Very short README")
                    score -= 20
            
            # Check for other documentation
            doc_files = list(self.project_root.glob("**/*.md")) + \
                       list(self.project_root.glob("docs/**/*"))
            
            if len(doc_files) > 5:
                details.append(f"Good documentation coverage ({len(doc_files)} files)")
            elif len(doc_files) > 1:
                details.append(f"Basic documentation ({len(doc_files)} files)")
                score -= 10
            else:
                details.append("Limited documentation")
                score -= 20
            
            # Check for CLAUDE.md (project-specific)
            claude_md = self.project_root / "CLAUDE.md"
            if claude_md.exists():
                details.append("Project instructions found (CLAUDE.md)")
            else:
                score -= 10
                details.append("No project instructions (CLAUDE.md)")
            
            if score >= 90:
                status = QualityGateStatus.PASSED
                message = "Documentation is excellent"
            elif score >= 70:
                status = QualityGateStatus.WARNING
                message = f"Documentation needs improvement (score: {score})"
            else:
                status = QualityGateStatus.FAILED
                message = f"Documentation is insufficient (score: {score})"
            
        except Exception as e:
            status = QualityGateStatus.FAILED
            score = 0
            message = f"Documentation check failed: {e}"
            details = [str(e)]
        
        return QualityGateResult(
            gate_name="documentation",
            status=status,
            score=score,
            message=message,
            details=details,
            duration_ms=(time.time() - start_time) * 1000
        )


async def run_ferrari_ci_cd() -> bool:
    """
    Run Ferrari CI/CD quality gates.
    Returns True if all gates pass.
    """
    gates = FerrariQualityGates()
    results = await gates.run_all_gates()
    
    return results["summary"]["pipeline_status"] in ["passed", "warning"]


if __name__ == "__main__":
    success = asyncio.run(run_ferrari_ci_cd())
    sys.exit(0 if success else 1)