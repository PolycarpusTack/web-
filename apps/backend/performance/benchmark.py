"""
Performance Benchmarking and Optimization Suite for Web+ Backend

This module provides comprehensive performance testing and baseline establishment
to ensure our Ferrari runs at peak performance.
"""
import asyncio
import time
import statistics
import psutil
import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a single performance metric."""
    name: str
    value: float
    unit: str
    timestamp: str
    baseline: Optional[float] = None
    threshold: Optional[float] = None
    status: str = "unknown"  # "good", "warning", "critical"


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    test_name: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: Optional[float] = None
    error_rate_percent: float = 0.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class PerformanceMonitor:
    """Monitor system performance during benchmarks."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = None
        self.start_time = None
        
    def start(self):
        """Start monitoring."""
        self.initial_memory = self.process.memory_info().rss
        self.start_time = time.time()
        
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        current_memory = self.process.memory_info().rss
        memory_delta_mb = (current_memory - self.initial_memory) / (1024 * 1024)
        cpu_percent = self.process.cpu_percent()
        
        return {
            "memory_usage_mb": memory_delta_mb,
            "cpu_usage_percent": cpu_percent,
            "duration_ms": (time.time() - self.start_time) * 1000
        }


class DatabaseBenchmark:
    """Database performance benchmarks."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def benchmark_user_operations(self, num_operations: int = 100) -> BenchmarkResult:
        """Benchmark user CRUD operations."""
        monitor = PerformanceMonitor()
        monitor.start()
        
        errors = 0
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from db import crud
            
            # Create users
            for i in range(num_operations):
                try:
                    user_data = {
                        "username": f"perf_user_{i}_{int(time.time())}",
                        "email": f"perf{i}_{int(time.time())}@test.com",
                        "password": "testpass123",
                        "full_name": f"Performance User {i}"
                    }
                    await crud.create_user(self.db, user_data)
                except Exception as e:
                    errors += 1
                    logger.warning(f"User creation error: {e}")
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Database benchmark failed: {e}")
            errors = num_operations
        
        end_time = time.time()
        metrics = monitor.get_current_metrics()
        
        duration_ms = (end_time - start_time) * 1000
        throughput = (num_operations - errors) / (duration_ms / 1000) if duration_ms > 0 else 0
        error_rate = (errors / num_operations) * 100
        
        return BenchmarkResult(
            test_name="database_user_operations",
            duration_ms=duration_ms,
            memory_usage_mb=metrics["memory_usage_mb"],
            cpu_usage_percent=metrics["cpu_usage_percent"],
            throughput_ops_per_sec=throughput,
            error_rate_percent=error_rate
        )
    
    async def benchmark_query_performance(self) -> BenchmarkResult:
        """Benchmark database query performance."""
        monitor = PerformanceMonitor()
        monitor.start()
        
        start_time = time.time()
        errors = 0
        
        try:
            # Test various query patterns
            from sqlalchemy import text
            
            # Simple SELECT
            await self.db.execute(text("SELECT 1"))
            
            # Table scan (if users exist)
            await self.db.execute(text("SELECT COUNT(*) FROM users"))
            
            # Index usage
            await self.db.execute(text("SELECT * FROM users WHERE username = 'nonexistent'"))
            
        except Exception as e:
            logger.error(f"Query benchmark failed: {e}")
            errors += 1
        
        end_time = time.time()
        metrics = monitor.get_current_metrics()
        
        return BenchmarkResult(
            test_name="database_query_performance",
            duration_ms=(end_time - start_time) * 1000,
            memory_usage_mb=metrics["memory_usage_mb"],
            cpu_usage_percent=metrics["cpu_usage_percent"],
            error_rate_percent=(errors / 3) * 100  # 3 queries total
        )


class APIBenchmark:
    """API endpoint performance benchmarks."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def benchmark_health_endpoint(self, num_requests: int = 50) -> BenchmarkResult:
        """Benchmark health check endpoint."""
        monitor = PerformanceMonitor()
        monitor.start()
        
        errors = 0
        response_times = []
        
        for i in range(num_requests):
            try:
                start_req = time.time()
                response = await self.client.get("/health")
                end_req = time.time()
                
                if response.status_code != 200:
                    errors += 1
                else:
                    response_times.append((end_req - start_req) * 1000)
                    
            except Exception as e:
                errors += 1
                logger.warning(f"Health check request failed: {e}")
        
        metrics = monitor.get_current_metrics()
        
        avg_response_time = statistics.mean(response_times) if response_times else 0
        throughput = len(response_times) / (metrics["duration_ms"] / 1000) if metrics["duration_ms"] > 0 else 0
        error_rate = (errors / num_requests) * 100
        
        return BenchmarkResult(
            test_name="api_health_endpoint",
            duration_ms=avg_response_time,
            memory_usage_mb=metrics["memory_usage_mb"],
            cpu_usage_percent=metrics["cpu_usage_percent"],
            throughput_ops_per_sec=throughput,
            error_rate_percent=error_rate
        )
    
    async def benchmark_auth_endpoints(self, num_requests: int = 10) -> BenchmarkResult:
        """Benchmark authentication endpoints."""
        monitor = PerformanceMonitor()
        monitor.start()
        
        errors = 0
        
        for i in range(num_requests):
            try:
                # Test registration
                user_data = {
                    "username": f"bench_user_{i}_{int(time.time())}",
                    "email": f"bench{i}_{int(time.time())}@test.com",
                    "password": "testpass123",
                    "full_name": f"Benchmark User {i}"
                }
                
                response = await self.client.post("/auth/register", json=user_data)
                if response.status_code not in [201, 409]:  # 409 for duplicate
                    errors += 1
                    
            except Exception as e:
                errors += 1
                logger.warning(f"Auth benchmark request failed: {e}")
        
        metrics = monitor.get_current_metrics()
        
        throughput = (num_requests - errors) / (metrics["duration_ms"] / 1000) if metrics["duration_ms"] > 0 else 0
        error_rate = (errors / num_requests) * 100
        
        return BenchmarkResult(
            test_name="api_auth_endpoints",
            duration_ms=metrics["duration_ms"],
            memory_usage_mb=metrics["memory_usage_mb"],
            cpu_usage_percent=metrics["cpu_usage_percent"],
            throughput_ops_per_sec=throughput,
            error_rate_percent=error_rate
        )


class FerrariPerformanceSuite:
    """Main performance testing suite for the Ferrari backend."""
    
    def __init__(self, db: AsyncSession = None, api_base_url: str = "http://localhost:8000"):
        self.db = db
        self.api_base_url = api_base_url
        self.results_dir = Path("performance_results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all performance benchmarks."""
        logger.info("🏎️ Starting Ferrari Performance Benchmark Suite")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "benchmarks": {},
            "summary": {}
        }
        
        # Database benchmarks
        if self.db:
            logger.info("Running database benchmarks...")
            db_benchmark = DatabaseBenchmark(self.db)
            
            try:
                results["benchmarks"]["db_user_ops"] = asdict(
                    await db_benchmark.benchmark_user_operations(50)
                )
                results["benchmarks"]["db_query_perf"] = asdict(
                    await db_benchmark.benchmark_query_performance()
                )
            except Exception as e:
                logger.error(f"Database benchmark failed: {e}")
                results["benchmarks"]["db_error"] = str(e)
        
        # API benchmarks
        logger.info("Running API benchmarks...")
        try:
            async with APIBenchmark(self.api_base_url) as api_benchmark:
                results["benchmarks"]["api_health"] = asdict(
                    await api_benchmark.benchmark_health_endpoint(25)
                )
                results["benchmarks"]["api_auth"] = asdict(
                    await api_benchmark.benchmark_auth_endpoints(5)
                )
        except Exception as e:
            logger.error(f"API benchmark failed: {e}")
            results["benchmarks"]["api_error"] = str(e)
        
        # Generate summary
        results["summary"] = self._generate_summary(results["benchmarks"])
        
        # Save results
        results_file = self.results_dir / f"benchmark_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📊 Benchmark results saved to: {results_file}")
        return results
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for the benchmark."""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "platform": os.name
        }
    
    def _generate_summary(self, benchmarks: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary and score."""
        summary = {
            "overall_score": 0,
            "performance_grade": "F",
            "issues": [],
            "recommendations": []
        }
        
        scores = []
        
        # Analyze each benchmark
        for test_name, result in benchmarks.items():
            if isinstance(result, dict) and "duration_ms" in result:
                score = self._calculate_test_score(test_name, result)
                scores.append(score)
                
                if score < 70:
                    summary["issues"].append(f"{test_name}: Performance below expectations")
        
        # Calculate overall score
        if scores:
            summary["overall_score"] = sum(scores) / len(scores)
            
            if summary["overall_score"] >= 90:
                summary["performance_grade"] = "A"
            elif summary["overall_score"] >= 80:
                summary["performance_grade"] = "B"
            elif summary["overall_score"] >= 70:
                summary["performance_grade"] = "C"
            elif summary["overall_score"] >= 60:
                summary["performance_grade"] = "D"
            else:
                summary["performance_grade"] = "F"
        
        # Add recommendations
        if summary["overall_score"] < 80:
            summary["recommendations"].extend([
                "Consider database query optimization",
                "Review API endpoint response times",
                "Check for memory leaks",
                "Optimize database indexes"
            ])
        
        return summary


def _calculate_test_score(test_name: str, result: Dict[str, Any]) -> float:
    """Calculate a performance score for a test (0-100)."""
    score = 100
    
    # Penalize high response times (Phase 2 target: < 200ms for API)
    duration = result.get("duration_ms", 0)
    if "api" in test_name:
        if duration > 200:  # > 200ms (Phase 2 target)
            score -= 30
        elif duration > 150:  # > 150ms
            score -= 15
        elif duration > 100:  # > 100ms
            score -= 5
    elif "db" in test_name:
        if duration > 5000:  # > 5 seconds
            score -= 30
        elif duration > 2000:  # > 2 seconds
            score -= 15
        elif duration > 1000:  # > 1 second
            score -= 5
    
    # Penalize high error rates
    error_rate = result.get("error_rate_percent", 0)
    if error_rate > 10:
        score -= 40
    elif error_rate > 5:
        score -= 20
    elif error_rate > 1:
        score -= 10
    
    # Penalize low throughput
    throughput = result.get("throughput_ops_per_sec", 0)
    if throughput > 0:  # Only check if throughput is measured
        if throughput < 1:
            score -= 20
        elif throughput < 5:
            score -= 10
    
    # Penalize high memory usage
    memory_mb = result.get("memory_usage_mb", 0)
    if memory_mb > 500:  # > 500MB
        score -= 15
    elif memory_mb > 200:  # > 200MB
        score -= 5
    
    return max(0, score)


async def run_ferrari_performance_test(db: AsyncSession = None) -> bool:
    """
    Main function to run Ferrari performance tests.
    Returns True if performance is acceptable.
    """
    suite = FerrariPerformanceSuite(db)
    results = await suite.run_all_benchmarks()
    
    print("\n🏎️ FERRARI PERFORMANCE RESULTS")
    print("=" * 50)
    print(f"🎯 Overall Score: {results['summary']['overall_score']:.1f}/100")
    print(f"📊 Performance Grade: {results['summary']['performance_grade']}")
    
    if results['summary']['issues']:
        print("\n⚠️  Performance Issues:")
        for issue in results['summary']['issues']:
            print(f"  - {issue}")
    
    if results['summary']['recommendations']:
        print("\n💡 Recommendations:")
        for rec in results['summary']['recommendations']:
            print(f"  - {rec}")
    
    grade = results['summary']['performance_grade']
    if grade in ['A', 'B']:
        print("\n🏁 Ferrari is READY TO RACE! Performance is excellent!")
        return True
    elif grade == 'C':
        print("\n🏃 Ferrari performance is acceptable but could be improved")
        return True
    else:
        print("\n🔧 Ferrari needs performance tuning before racing")
        return False


if __name__ == "__main__":
    # Simple test without database
    asyncio.run(run_ferrari_performance_test())