#!/usr/bin/env python3
"""
Simple Ferrari Performance Test
No external dependencies required.
"""
import time
import os
import json
from pathlib import Path

def run_simple_performance_test():
    """Run basic performance tests."""
    print("🏎️ Ferrari Simple Performance Test")
    print("=" * 40)
    
    results = {
        "timestamp": time.time(),
        "tests": {},
        "score": 0
    }
    
    # Test 1: CPU Performance
    print("🧮 Testing CPU Performance...")
    start_time = time.time()
    
    # Simple CPU-intensive task
    result = 0
    for i in range(500000):
        result += i * 2
    
    cpu_duration = time.time() - start_time
    cpu_ops_per_sec = 500000 / cpu_duration if cpu_duration > 0 else 0
    
    results["tests"]["cpu_performance"] = {
        "duration_ms": cpu_duration * 1000,
        "operations": 500000,
        "ops_per_sec": cpu_ops_per_sec
    }
    
    print(f"  Duration: {cpu_duration * 1000:.1f}ms")
    print(f"  Throughput: {cpu_ops_per_sec:.0f} ops/sec")
    
    # Test 2: Memory Allocation
    print("\n💾 Testing Memory Allocation...")
    start_time = time.time()
    
    # Memory allocation test
    data = []
    for i in range(50000):
        data.append(f"test_string_{i}")
    
    memory_duration = time.time() - start_time
    allocs_per_sec = 50000 / memory_duration if memory_duration > 0 else 0
    
    results["tests"]["memory_performance"] = {
        "duration_ms": memory_duration * 1000,
        "allocations": 50000,
        "allocs_per_sec": allocs_per_sec
    }
    
    print(f"  Duration: {memory_duration * 1000:.1f}ms")
    print(f"  Throughput: {allocs_per_sec:.0f} allocs/sec")
    
    # Test 3: String Operations
    print("\n📝 Testing String Operations...")
    start_time = time.time()
    
    # String manipulation test
    text = "Ferrari performance test "
    for i in range(10000):
        text += f"iteration_{i} "
        if len(text) > 100000:  # Prevent excessive memory usage
            text = "Ferrari performance test "
    
    string_duration = time.time() - start_time
    string_ops_per_sec = 10000 / string_duration if string_duration > 0 else 0
    
    results["tests"]["string_performance"] = {
        "duration_ms": string_duration * 1000,
        "operations": 10000,
        "ops_per_sec": string_ops_per_sec
    }
    
    print(f"  Duration: {string_duration * 1000:.1f}ms")
    print(f"  Throughput: {string_ops_per_sec:.0f} string ops/sec")
    
    # Test 4: File I/O
    print("\n📁 Testing File I/O...")
    start_time = time.time()
    
    test_file = Path("perf_test.tmp")
    try:
        # Write test
        with open(test_file, "w") as f:
            for i in range(5000):
                f.write(f"test line {i}\\n")
        
        # Read test
        with open(test_file, "r") as f:
            lines = f.readlines()
        
        io_duration = time.time() - start_time
        io_ops_per_sec = 10000 / io_duration if io_duration > 0 else 0  # read + write operations
        
        results["tests"]["io_performance"] = {
            "duration_ms": io_duration * 1000,
            "lines_written": 5000,
            "lines_read": len(lines),
            "io_ops_per_sec": io_ops_per_sec
        }
        
        print(f"  Duration: {io_duration * 1000:.1f}ms")
        print(f"  Throughput: {io_ops_per_sec:.0f} I/O ops/sec")
        
    except Exception as e:
        print(f"  ❌ I/O test failed: {e}")
        results["tests"]["io_performance"] = {"error": str(e)}
    finally:
        if test_file.exists():
            test_file.unlink()
    
    # Calculate Overall Score
    score = 100
    
    # CPU score (target: > 500k ops/sec)
    cpu_ops = results["tests"]["cpu_performance"]["ops_per_sec"]
    if cpu_ops < 250000:
        score -= 25
    elif cpu_ops < 400000:
        score -= 15
    elif cpu_ops < 500000:
        score -= 5
    
    # Memory score (target: > 25k allocs/sec)
    mem_ops = results["tests"]["memory_performance"]["allocs_per_sec"]
    if mem_ops < 12500:
        score -= 25
    elif mem_ops < 20000:
        score -= 15
    elif mem_ops < 25000:
        score -= 5
    
    # String operations score (target: > 5k ops/sec)
    str_ops = results["tests"]["string_performance"]["ops_per_sec"]
    if str_ops < 2500:
        score -= 20
    elif str_ops < 4000:
        score -= 10
    elif str_ops < 5000:
        score -= 5
    
    # I/O score (target: > 5k ops/sec)
    if "io_performance" in results["tests"] and "io_ops_per_sec" in results["tests"]["io_performance"]:
        io_ops = results["tests"]["io_performance"]["io_ops_per_sec"]
        if io_ops < 2500:
            score -= 20
        elif io_ops < 4000:
            score -= 10
        elif io_ops < 5000:
            score -= 5
    else:
        score -= 20  # I/O test failed
    
    results["score"] = max(0, score)
    
    # Determine grade and status
    if score >= 90:
        grade = "A"
        status = "🏁 READY TO RACE! Excellent performance!"
    elif score >= 80:
        grade = "B"
        status = "🏃 Good performance, ready for staging"
    elif score >= 70:
        grade = "C"
        status = "⚡ Acceptable performance"
    elif score >= 60:
        grade = "D"
        status = "🔧 Needs improvement"
    else:
        grade = "F"
        status = "🚫 Poor performance, needs optimization"
    
    # Results
    print("\n" + "=" * 40)
    print("🏎️ FERRARI PERFORMANCE RESULTS")
    print("=" * 40)
    print(f"🎯 Overall Score: {score}/100")
    print(f"📊 Performance Grade: {grade}")
    print(f"🚦 Status: {status}")
    
    # Performance breakdown
    print("\n📊 Performance Breakdown:")
    print(f"  CPU: {cpu_ops:.0f} ops/sec")
    print(f"  Memory: {mem_ops:.0f} allocs/sec")
    print(f"  String: {str_ops:.0f} ops/sec")
    if "io_ops_per_sec" in results["tests"].get("io_performance", {}):
        print(f"  I/O: {results['tests']['io_performance']['io_ops_per_sec']:.0f} ops/sec")
    
    if score < 80:
        print("\n💡 Performance Recommendations:")
        if cpu_ops < 400000:
            print("  - CPU performance below optimal, consider closing other applications")
        if mem_ops < 20000:
            print("  - Memory allocation performance could be improved")
        if str_ops < 4000:
            print("  - String operations are slow, check Python version")
        if "io_performance" not in results["tests"] or results["tests"]["io_performance"].get("io_ops_per_sec", 0) < 4000:
            print("  - File I/O performance needs improvement")
    
    # Save results
    results_dir = Path("performance_results")
    results_dir.mkdir(exist_ok=True)
    results_file = results_dir / f"simple_baseline_{int(time.time())}.json"
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    print("\n🏎️ Ferrari Performance Baseline Established!")
    
    return score >= 70

if __name__ == "__main__":
    success = run_simple_performance_test()
    if success:
        print("\n✅ Ferrari passes performance baseline!")
    else:
        print("\n❌ Ferrari needs performance tuning!")
    exit(0 if success else 1)