#!/usr/bin/env python3
"""
Complete Test Runner
Runs all available tests and provides comprehensive status report
"""

import sys
import os
import subprocess
import time
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test_file(test_file: str) -> Dict[str, Any]:
    """Run a single test file and return results"""
    print(f"\n🧪 Running {test_file}...")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        end_time = time.time()
        
        return {
            "file": test_file,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_ms": (end_time - start_time) * 1000,
            "status": "PASS" if result.returncode == 0 else "FAIL"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "file": test_file,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Test timed out after 60 seconds",
            "duration_ms": 60000,
            "status": "TIMEOUT"
        }
    except Exception as e:
        return {
            "file": test_file,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "duration_ms": 0,
            "status": "ERROR"
        }


def main():
    """Run all tests and provide comprehensive report"""
    print("🚀 Complete Test Runner")
    print("=" * 60)
    
    # Define all test files
    test_files = [
        "run_production_tests.py",
        "test_end_to_end_api.py",
        "test_llm_safety.py",
        "test_rag_citations.py",
        "test_api_integration.py",
        "test_failure_modes.py",
        "test_unit_agents.py",
        "test_load_performance.py"
    ]
    
    results = []
    
    for test_file in test_files:
        if os.path.exists(test_file):
            result = run_test_file(test_file)
            results.append(result)
            
            # Print immediate result
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"   {status_icon} {test_file}: {result['status']} ({result['duration_ms']:.1f}ms)")
            
            # Print key errors for failed tests
            if result["status"] != "PASS" and result["stderr"]:
                error_lines = result["stderr"].split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        print(f"      Error: {line.strip()}")
        else:
            print(f"   ⚠️  {test_file}: NOT FOUND")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
    error = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)
    
    # Categorize tests
    working_tests = []
    failing_tests = []
    
    for result in results:
        if result["status"] == "PASS":
            working_tests.append(result["file"])
        else:
            failing_tests.append({
                "file": result["file"],
                "status": result["status"],
                "error": result["stderr"].split('\n')[0] if result["stderr"] else "Unknown error"
            })
    
    print(f"\n📈 Test Summary:")
    print(f"   Total: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   ⏱️ Timeout: {timeout}")
    print(f"   💥 Error: {error}")
    print(f"   📊 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "   📊 Success Rate: 0%")
    
    print(f"\n✅ Working Tests:")
    for test in working_tests:
        print(f"   - {test}")
    
    if failing_tests:
        print(f"\n❌ Failing Tests:")
        for test in failing_tests:
            print(f"   - {test['file']}: {test['status']} ({test['error']})")
    
    # System status assessment
    print(f"\n🎯 System Status Assessment:")
    
    if passed >= 6:
        print("   🟢 STRONG: Most tests passing, system largely functional")
    elif passed >= 4:
        print("   🟡 MODERATE: Some tests passing, system partially functional")
    else:
        print("   🔴 WEAK: Few tests passing, system needs significant work")
    
    # Specific functionality assessment
    print(f"\n🔧 Functionality Status:")
    
    production_tests_passed = any("run_production_tests.py" in t for t in working_tests)
    api_tests_passed = any("test_end_to_end_api.py" in t for t in working_tests)
    llm_tests_passed = any("test_llm_safety.py" in t for t in working_tests)
    
    print(f"   🏭 Production Tests: {'✅ WORKING' if production_tests_passed else '❌ FAILING'}")
    print(f"   🌐 API Endpoints: {'✅ WORKING' if api_tests_passed else '❌ FAILING'}")
    print(f"   🤖 LLM Safety: {'✅ WORKING' if llm_tests_passed else '❌ FAILING'}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if failed > 0:
        print(f"   🔧 Fix {failed} failing test(s) to improve system reliability")
    
    if "test_unit_agents.py" in [t["file"] for t in failing_tests]:
        print(f"   📦 Fix import issues in unit tests")
    
    if "test_rag_citations.py" in [t["file"] for t in failing_tests]:
        print(f"   🔗 Fix module import paths in RAG tests")
    
    if production_tests_passed and api_tests_passed:
        print(f"   ✅ Core functionality working - focus on remaining test issues")
    
    return results


if __name__ == "__main__":
    main()
