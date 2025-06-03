"""
Ferrari Health Monitoring and Observability Suite

This module provides comprehensive health monitoring, metrics collection,
and observability for the Web+ backend to ensure our Ferrari runs smoothly.
"""
import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """A single health metric."""
    name: str
    value: Any
    status: HealthStatus
    message: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ComponentHealth:
    """Health status of a system component."""
    component: str
    status: HealthStatus
    metrics: List[HealthMetric]
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class FerrariHealthMonitor:
    """Main health monitoring system for Ferrari backend."""
    
    def __init__(self):
        self.results_dir = Path("monitoring_results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def check_all_systems(self) -> Dict[str, Any]:
        """Check health of all Ferrari systems."""
        logger.info("🏎️ Starting Ferrari Health Check...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": HealthStatus.HEALTHY.value,
            "components": {},
            "summary": {
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "total_components": 0
            }
        }
        
        # Check each component
        components = [
            self._check_system_resources(),
            self._check_database_health(),
            self._check_api_endpoints(),
            self._check_file_system(),
            self._check_security_status(),
            self._check_performance_metrics()
        ]
        
        for component_check in components:
            try:
                component_health = await component_check
                health_report["components"][component_health.component] = asdict(component_health)
                
                # Update summary
                health_report["summary"]["total_components"] += 1
                if component_health.status == HealthStatus.HEALTHY:
                    health_report["summary"]["healthy"] += 1
                elif component_health.status == HealthStatus.WARNING:
                    health_report["summary"]["warning"] += 1
                elif component_health.status == HealthStatus.CRITICAL:
                    health_report["summary"]["critical"] += 1
                    
            except Exception as e:
                logger.error(f"Health check failed for component: {e}")
                health_report["components"]["error"] = {
                    "component": "unknown",
                    "status": HealthStatus.CRITICAL.value,
                    "error_message": str(e)
                }
                health_report["summary"]["critical"] += 1
                health_report["summary"]["total_components"] += 1
        
        # Determine overall status
        if health_report["summary"]["critical"] > 0:
            health_report["overall_status"] = HealthStatus.CRITICAL.value
        elif health_report["summary"]["warning"] > 0:
            health_report["overall_status"] = HealthStatus.WARNING.value
        else:
            health_report["overall_status"] = HealthStatus.HEALTHY.value
        
        # Save health report
        health_file = self.results_dir / f"health_check_{int(time.time())}.json"
        with open(health_file, "w") as f:
            json.dump(health_report, f, indent=2, default=str)
        
        logger.info(f"📊 Health report saved to: {health_file}")
        return health_report
    
    async def _check_system_resources(self) -> ComponentHealth:
        """Check system resource health."""
        start_time = time.time()
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Check disk space
            import shutil
            disk_usage = shutil.disk_usage(".")
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            usage_percent = ((total_gb - free_gb) / total_gb) * 100
            
            if usage_percent > 90:
                disk_status = HealthStatus.CRITICAL
                disk_message = f"Disk usage critical: {usage_percent:.1f}%"
                status = HealthStatus.CRITICAL
            elif usage_percent > 80:
                disk_status = HealthStatus.WARNING
                disk_message = f"Disk usage high: {usage_percent:.1f}%"
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            else:
                disk_status = HealthStatus.HEALTHY
                disk_message = f"Disk usage normal: {usage_percent:.1f}%"
            
            metrics.append(HealthMetric(
                name="disk_usage_percent",
                value=round(usage_percent, 1),
                status=disk_status,
                message=disk_message
            ))
            
            # Check available memory (simplified)
            import os
            try:
                # Try to allocate and release memory
                test_data = bytearray(10 * 1024 * 1024)  # 10MB
                del test_data
                
                metrics.append(HealthMetric(
                    name="memory_allocation",
                    value="success",
                    status=HealthStatus.HEALTHY,
                    message="Memory allocation test passed"
                ))
            except MemoryError:
                metrics.append(HealthMetric(
                    name="memory_allocation",
                    value="failed",
                    status=HealthStatus.CRITICAL,
                    message="Memory allocation failed"
                ))
                status = HealthStatus.CRITICAL
            
        except Exception as e:
            metrics.append(HealthMetric(
                name="system_resources",
                value="error",
                status=HealthStatus.CRITICAL,
                message=f"System resource check failed: {e}"
            ))
            status = HealthStatus.CRITICAL
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            component="system_resources",
            status=status,
            metrics=metrics,
            response_time_ms=response_time
        )
    
    async def _check_database_health(self) -> ComponentHealth:
        """Check database connectivity and health."""
        start_time = time.time()
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Try to import database modules
            from db.database import get_async_session
            from sqlalchemy import text
            
            # Test database connection
            async with get_async_session() as db:
                await db.execute(text("SELECT 1"))
                
                metrics.append(HealthMetric(
                    name="database_connection",
                    value="connected",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful"
                ))
                
                # Check if we can query basic tables
                try:
                    result = await db.execute(text("SELECT COUNT(*) FROM users"))
                    user_count = result.scalar()
                    
                    metrics.append(HealthMetric(
                        name="user_table_access",
                        value=user_count,
                        status=HealthStatus.HEALTHY,
                        message=f"User table accessible, {user_count} users"
                    ))
                except Exception as table_error:
                    metrics.append(HealthMetric(
                        name="user_table_access",
                        value="error",
                        status=HealthStatus.WARNING,
                        message=f"User table access issue: {table_error}"
                    ))
                    if status == HealthStatus.HEALTHY:
                        status = HealthStatus.WARNING
        
        except ImportError as e:
            metrics.append(HealthMetric(
                name="database_modules",
                value="missing",
                status=HealthStatus.WARNING,
                message=f"Database modules not available: {e}"
            ))
            status = HealthStatus.WARNING
        except Exception as e:
            metrics.append(HealthMetric(
                name="database_connection",
                value="failed",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {e}"
            ))
            status = HealthStatus.CRITICAL
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            component="database",
            status=status,
            metrics=metrics,
            response_time_ms=response_time
        )
    
    async def _check_api_endpoints(self) -> ComponentHealth:
        """Check API endpoint health."""
        start_time = time.time()
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Check if FastAPI app is importable
            from main import app
            
            metrics.append(HealthMetric(
                name="fastapi_app",
                value="importable",
                status=HealthStatus.HEALTHY,
                message="FastAPI application loads successfully"
            ))
            
            # Check if key routes are defined
            route_count = len(app.routes)
            if route_count > 10:
                route_status = HealthStatus.HEALTHY
                route_message = f"API routes healthy: {route_count} routes"
            elif route_count > 5:
                route_status = HealthStatus.WARNING
                route_message = f"Limited API routes: {route_count} routes"
            else:
                route_status = HealthStatus.CRITICAL
                route_message = f"Few API routes: {route_count} routes"
                status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                name="api_routes",
                value=route_count,
                status=route_status,
                message=route_message
            ))
            
        except ImportError as e:
            metrics.append(HealthMetric(
                name="fastapi_app",
                value="failed",
                status=HealthStatus.CRITICAL,
                message=f"FastAPI app import failed: {e}"
            ))
            status = HealthStatus.CRITICAL
        except Exception as e:
            metrics.append(HealthMetric(
                name="api_endpoints",
                value="error",
                status=HealthStatus.WARNING,
                message=f"API endpoint check failed: {e}"
            ))
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.WARNING
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            component="api_endpoints",
            status=status,
            metrics=metrics,
            response_time_ms=response_time
        )
    
    async def _check_file_system(self) -> ComponentHealth:
        """Check file system health."""
        start_time = time.time()
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Test file creation and deletion
            test_file = Path("health_test.tmp")
            test_content = "Ferrari health check test"
            
            # Write test
            with open(test_file, "w") as f:
                f.write(test_content)
            
            # Read test
            with open(test_file, "r") as f:
                read_content = f.read()
            
            # Verify content
            if read_content == test_content:
                metrics.append(HealthMetric(
                    name="file_operations",
                    value="success",
                    status=HealthStatus.HEALTHY,
                    message="File read/write operations working"
                ))
            else:
                metrics.append(HealthMetric(
                    name="file_operations",
                    value="mismatch",
                    status=HealthStatus.WARNING,
                    message="File content mismatch"
                ))
                status = HealthStatus.WARNING
            
            # Cleanup
            test_file.unlink()
            
            # Check critical directories
            critical_dirs = ["logs", "uploads", "performance_results", "monitoring_results"]
            missing_dirs = []
            
            for dir_name in critical_dirs:
                dir_path = Path(dir_name)
                if not dir_path.exists():
                    missing_dirs.append(dir_name)
                    dir_path.mkdir(exist_ok=True)  # Create if missing
            
            if missing_dirs:
                metrics.append(HealthMetric(
                    name="critical_directories",
                    value=f"created: {', '.join(missing_dirs)}",
                    status=HealthStatus.WARNING,
                    message=f"Created missing directories: {', '.join(missing_dirs)}"
                ))
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            else:
                metrics.append(HealthMetric(
                    name="critical_directories",
                    value="present",
                    status=HealthStatus.HEALTHY,
                    message="All critical directories present"
                ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                name="file_system",
                value="error",
                status=HealthStatus.CRITICAL,
                message=f"File system check failed: {e}"
            ))
            status = HealthStatus.CRITICAL
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            component="file_system",
            status=status,
            metrics=metrics,
            response_time_ms=response_time
        )
    
    async def _check_security_status(self) -> ComponentHealth:
        """Check security configuration health."""
        start_time = time.time()
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Check security middleware
            security_files = [
                Path("security/security_middleware.py"),
                Path("security/security_audit.py")
            ]
            
            missing_security = []
            for sec_file in security_files:
                if not sec_file.exists():
                    missing_security.append(sec_file.name)
            
            if missing_security:
                metrics.append(HealthMetric(
                    name="security_files",
                    value=f"missing: {', '.join(missing_security)}",
                    status=HealthStatus.WARNING,
                    message=f"Missing security files: {', '.join(missing_security)}"
                ))
                status = HealthStatus.WARNING
            else:
                metrics.append(HealthMetric(
                    name="security_files",
                    value="present",
                    status=HealthStatus.HEALTHY,
                    message="Security files present"
                ))
            
            # Check environment configuration
            env_file = Path(".env")
            gitignore = Path(".gitignore")
            
            if env_file.exists() and gitignore.exists():
                gitignore_content = gitignore.read_text()
                if ".env" in gitignore_content:
                    metrics.append(HealthMetric(
                        name="env_security",
                        value="secured",
                        status=HealthStatus.HEALTHY,
                        message=".env file properly ignored"
                    ))
                else:
                    metrics.append(HealthMetric(
                        name="env_security",
                        value="exposed",
                        status=HealthStatus.CRITICAL,
                        message=".env file not in .gitignore"
                    ))
                    status = HealthStatus.CRITICAL
            else:
                metrics.append(HealthMetric(
                    name="env_security",
                    value="unknown",
                    status=HealthStatus.WARNING,
                    message="Environment configuration unclear"
                ))
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            
        except Exception as e:
            metrics.append(HealthMetric(
                name="security_status",
                value="error",
                status=HealthStatus.WARNING,
                message=f"Security check failed: {e}"
            ))
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.WARNING
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            component="security",
            status=status,
            metrics=metrics,
            response_time_ms=response_time
        )
    
    async def _check_performance_metrics(self) -> ComponentHealth:
        """Check performance baseline health."""
        start_time = time.time()
        metrics = []
        status = HealthStatus.HEALTHY
        
        try:
            # Check if performance results exist
            perf_dir = Path("performance_results")
            if perf_dir.exists():
                perf_files = list(perf_dir.glob("*.json"))
                if perf_files:
                    # Get latest performance result
                    latest_file = max(perf_files, key=lambda x: x.stat().st_mtime)
                    
                    with open(latest_file, "r") as f:
                        perf_data = json.load(f)
                    
                    score = perf_data.get("score", 0)
                    if score >= 80:
                        perf_status = HealthStatus.HEALTHY
                        perf_message = f"Performance excellent: {score}/100"
                    elif score >= 60:
                        perf_status = HealthStatus.WARNING
                        perf_message = f"Performance acceptable: {score}/100"
                        status = HealthStatus.WARNING
                    else:
                        perf_status = HealthStatus.CRITICAL
                        perf_message = f"Performance poor: {score}/100"
                        status = HealthStatus.CRITICAL
                    
                    metrics.append(HealthMetric(
                        name="performance_score",
                        value=score,
                        status=perf_status,
                        message=perf_message
                    ))
                else:
                    metrics.append(HealthMetric(
                        name="performance_baseline",
                        value="missing",
                        status=HealthStatus.WARNING,
                        message="No performance baseline found"
                    ))
                    status = HealthStatus.WARNING
            else:
                metrics.append(HealthMetric(
                    name="performance_directory",
                    value="missing",
                    status=HealthStatus.WARNING,
                    message="Performance results directory missing"
                ))
                status = HealthStatus.WARNING
            
            # Quick performance test
            quick_start = time.time()
            test_result = sum(i for i in range(10000))
            quick_duration = (time.time() - quick_start) * 1000
            
            if quick_duration < 10:
                quick_status = HealthStatus.HEALTHY
                quick_message = f"Quick test fast: {quick_duration:.1f}ms"
            elif quick_duration < 50:
                quick_status = HealthStatus.WARNING
                quick_message = f"Quick test slow: {quick_duration:.1f}ms"
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING
            else:
                quick_status = HealthStatus.CRITICAL
                quick_message = f"Quick test very slow: {quick_duration:.1f}ms"
                status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                name="quick_performance_test",
                value=round(quick_duration, 1),
                status=quick_status,
                message=quick_message
            ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                name="performance_check",
                value="error",
                status=HealthStatus.WARNING,
                message=f"Performance check failed: {e}"
            ))
            if status == HealthStatus.HEALTHY:
                status = HealthStatus.WARNING
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            component="performance",
            status=status,
            metrics=metrics,
            response_time_ms=response_time
        )


async def run_ferrari_health_check() -> Dict[str, Any]:
    """Run complete Ferrari health check."""
    monitor = FerrariHealthMonitor()
    return await monitor.check_all_systems()


def print_health_report(health_report: Dict[str, Any]):
    """Print a formatted health report."""
    print("🏎️ FERRARI HEALTH CHECK REPORT")
    print("=" * 50)
    
    overall_status = health_report["overall_status"]
    if overall_status == "healthy":
        print("🟢 Overall Status: HEALTHY - Ferrari is ready to race!")
    elif overall_status == "warning":
        print("🟡 Overall Status: WARNING - Ferrari needs attention")
    else:
        print("🔴 Overall Status: CRITICAL - Ferrari needs immediate repair!")
    
    print(f"📊 Component Summary:")
    print(f"  ✅ Healthy: {health_report['summary']['healthy']}")
    print(f"  ⚠️  Warning: {health_report['summary']['warning']}")
    print(f"  ❌ Critical: {health_report['summary']['critical']}")
    print(f"  📝 Total: {health_report['summary']['total_components']}")
    
    print("\n🔧 Component Details:")
    for comp_name, comp_data in health_report["components"].items():
        status = str(comp_data["status"]).replace("HealthStatus.", "").lower()
        if status == "healthy":
            status_icon = "✅"
        elif status == "warning":
            status_icon = "⚠️ "
        else:
            status_icon = "❌"
        
        response_time = comp_data.get("response_time_ms", 0)
        print(f"  {status_icon} {comp_name}: {status.upper()} ({response_time:.1f}ms)")
        
        # Show critical metrics
        for metric in comp_data.get("metrics", []):
            metric_status = str(metric["status"]).replace("HealthStatus.", "").lower()
            if metric_status in ["warning", "critical"]:
                print(f"    └─ {metric['message']}")


if __name__ == "__main__":
    async def main():
        health_report = await run_ferrari_health_check()
        print_health_report(health_report)
        
        overall_healthy = health_report["overall_status"] == "healthy"
        return overall_healthy
    
    success = asyncio.run(main())
    exit(0 if success else 1)