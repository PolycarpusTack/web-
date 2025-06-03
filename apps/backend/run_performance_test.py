#!/usr/bin/env python3
"""
Run Ferrari Performance Tests

Simple performance testing without external dependencies.
"""
import time
import psutil
import os
import json
from pathlib import Path

def run_ferrari_performance_baseline():
    """Run basic performance baseline tests."""
    print("🏎️ Ferrari Performance Baseline Test")
    print("=" * 40)
    
    results = {
        "timestamp": time.time(),
        "system_info": {},
        "tests": {},
        "score": 0
    }
    
    # System Information
    print("📊 Gathering System Information...")
    results["system_info"] = {
        "cpu_count": psutil.cpu_count(),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "disk_usage_percent": psutil.disk_usage("/").percent if os.name != "nt" else 0
    }
    
    print(f"  CPU Cores: {results['system_info']['cpu_count']}")
    print(f"  Memory: {results['system_info']['memory_available_gb']:.1f}GB available")
    print(f"  CPU Usage: {results['system_info']['cpu_percent']:.1f}%")
    
    # Test 1: CPU Performance
    print("\n🧮 Testing CPU Performance...")
    start_time = time.time()
    
    # Simple CPU-intensive task
    result = 0
    for i in range(1000000):
        result += i * 2
    
    cpu_duration = time.time() - start_time
    results["tests"]["cpu_performance"] = {
        "duration_ms": cpu_duration * 1000,
        "operations": 1000000,
        "ops_per_sec": 1000000 / cpu_duration
    }
    
    print(f"  Duration: {cpu_duration * 1000:.1f}ms")
    print(f"  Throughput: {results['tests']['cpu_performance']['ops_per_sec']:.0f} ops/sec")
    
    # Test 2: Memory Performance
    print("\n💾 Testing Memory Performance...")
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss
    
    # Memory allocation test
    data = []
    for i in range(100000):
        data.append(f"test_string_{i}")
    
    end_memory = psutil.Process().memory_info().rss
    memory_duration = time.time() - start_time
    memory_used_mb = (end_memory - start_memory) / (1024 * 1024)
    
    results["tests"]["memory_performance"] = {
        "duration_ms": memory_duration * 1000,
        "memory_used_mb": memory_used_mb,
        "allocations": 100000,
        "allocs_per_sec": 100000 / memory_duration
    }
    
    print(f"  Duration: {memory_duration * 1000:.1f}ms")
    print(f"  Memory Used: {memory_used_mb:.1f}MB")
    print(f"  Throughput: {results['tests']['memory_performance']['allocs_per_sec']:.0f} allocs/sec")
    
    # Test 3: File I/O Performance
    print("\n📁 Testing File I/O Performance...")
    start_time = time.time()
    
    test_file = Path("perf_test.tmp")
    try:
        # Write test
        with open(test_file, "w") as f:
            for i in range(10000):
                f.write(f"test line {i}\\n")
        
        # Read test
        with open(test_file, "r") as f:
            lines = f.readlines()
        
        io_duration = time.time() - start_time
        results["tests"]["io_performance"] = {
            "duration_ms": io_duration * 1000,
            "lines_written": 10000,
            "lines_read": len(lines),
            "io_ops_per_sec": 20000 / io_duration  # read + write operations
        }
        
        print(f"  Duration: {io_duration * 1000:.1f}ms")
        print(f"  Throughput: {results['tests']['io_performance']['io_ops_per_sec']:.0f} I/O ops/sec")
        
    except Exception as e:
        print(f"  ❌ I/O test failed: {e}")
        results["tests"]["io_performance"] = {"error": str(e)}
    finally:
        if test_file.exists():
            test_file.unlink()
    
    # Calculate Overall Score
    score = 100
    
    # CPU score (target: > 1M ops/sec)
    cpu_ops = results["tests"]["cpu_performance"]["ops_per_sec"]
    if cpu_ops < 500000:
        score -= 20
    elif cpu_ops < 750000:
        score -= 10
    
    # Memory score (target: > 50k allocs/sec)
    if "memory_performance" in results["tests"]:
        mem_ops = results["tests"]["memory_performance"]["allocs_per_sec"]
        if mem_ops < 25000:
            score -= 20
        elif mem_ops < 40000:
            score -= 10
    
    # I/O score (target: > 10k ops/sec)
    if "io_performance" in results["tests"] and "io_ops_per_sec" in results["tests"]["io_performance"]:
        io_ops = results["tests"]["io_performance"]["io_ops_per_sec"]
        if io_ops < 5000:
            score -= 20
        elif io_ops < 8000:
            score -= 10
    
    # System resource penalties
    if results["system_info"]["memory_available_gb"] < 2:
        score -= 15
    if results["system_info"]["cpu_percent"] > 80:
        score -= 10
    
    results["score"] = max(0, score)
    
    # Determine grade
    if score >= 90:
        grade = "A"
        status = "🏁 READY TO RACE!"
    elif score >= 80:
        grade = "B"
        status = "🏃 Good performance"
    elif score >= 70:
        grade = "C"
        status = "⚡ Acceptable performance"
    elif score >= 60:
        grade = "D"
        status = "🔧 Needs improvement"
    else:
        grade = "F"
        status = "🚫 Poor performance"
    
    # Results
    print("\n" + "=" * 40)
    print("🏎️ FERRARI PERFORMANCE RESULTS")
    print("=" * 40)
    print(f"🎯 Overall Score: {score}/100")
    print(f"📊 Performance Grade: {grade}")
    print(f"🚦 Status: {status}")
    
    if score < 80:
        print("\n💡 Performance Tips:")
        if cpu_ops < 750000:
            print("  - Consider upgrading CPU or closing other applications")
        if results["system_info"]["memory_available_gb"] < 4:
            print("  - Consider adding more RAM")
        if results["system_info"]["cpu_percent"] > 80:
            print("  - Reduce system load before running performance tests")
    
    # Save results
    results_dir = Path("performance_results")
    results_dir.mkdir(exist_ok=True)
    results_file = results_dir / f"baseline_{int(time.time())}.json"
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    return score >= 70

if __name__ == "__main__":
    success = run_ferrari_performance_baseline()
    exit(0 if success else 1)