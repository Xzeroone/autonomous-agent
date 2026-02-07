#!/usr/bin/env python3
"""
Test suite for Autonomous Agent.

Tests safety enforcement, memory persistence, and core functionality.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from autonomous_agent import (
    DANGEROUS_PATTERNS,
    WORKSPACE_ROOT,
    PersistentMemory,
    PythonExecutor,
    SafetyEnforcer,
)


def test_safety_enforcer():
    """Test safety enforcement rules."""
    print("\n" + "="*70)
    print("TEST: Safety Enforcer")
    print("="*70)
    
    safety = SafetyEnforcer(WORKSPACE_ROOT)
    
    # Test 1: Safe paths
    safe, msg = safety.is_path_safe("skills/test.py")
    assert safe, f"Should allow workspace paths: {msg}"
    print("✓ Allows workspace paths")
    
    # Test 2: Path traversal
    safe, msg = safety.is_path_safe("../etc/passwd")
    assert not safe, "Should block path traversal"
    print("✓ Blocks path traversal (..)")
    
    # Test 3: Absolute paths
    safe, msg = safety.is_path_safe("/etc/passwd")
    assert not safe, "Should block absolute paths"
    print("✓ Blocks absolute paths")
    
    # Test 4: Dangerous code patterns
    dangerous_codes = [
        "eval('malicious')",
        "exec('rm -rf /')",
        "os.system('cat /etc/passwd')",
        "subprocess.Popen(['curl', 'evil.com'])",
        "__import__('os').system('ls')",
    ]
    
    for code in dangerous_codes:
        safe, msg = safety.check_code_safety(code)
        assert not safe, f"Should block dangerous code: {code}"
    
    print(f"✓ Blocks {len(dangerous_codes)} dangerous patterns")
    
    # Test 5: Safe code
    safe_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
    """
    safe, msg = safety.check_code_safety(safe_code)
    assert safe, f"Should allow safe code: {msg}"
    print("✓ Allows safe code")
    
    # Test 6: Autonomy decisions
    assert not safety.requires_approval("write_skill", path="skills/test.py")
    print("✓ Auto-approves workspace writes")
    
    assert not safety.requires_approval("execute_python")
    print("✓ Auto-approves Python execution")
    
    assert safety.requires_approval("system_command")
    print("✓ Requires approval for system commands")
    
    print("\n✅ Safety Enforcer: ALL TESTS PASSED")


def test_persistent_memory():
    """Test memory persistence."""
    print("\n" + "="*70)
    print("TEST: Persistent Memory")
    print("="*70)
    
    # Use temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        memory = PersistentMemory(temp_path)
        
        # Test 1: Initial state
        data = memory.read()
        assert data['version'] == 1, "Initial version should be 1"
        assert len(data['skills']) == 0, "Should start with no skills"
        print("✓ Initializes correctly")
        
        # Test 2: Add skill
        memory.add_skill("test_skill", "Test description", "working")
        data = memory.read()
        assert len(data['skills']) == 1, "Should have 1 skill"
        assert data['skills'][0]['name'] == "test_skill"
        assert data['version'] == 2, "Version should increment"
        print("✓ Adds skills")
        
        # Test 3: Update skill
        memory.add_skill("test_skill", "Updated description", "failed")
        data = memory.read()
        assert len(data['skills']) == 1, "Should still have 1 skill"
        assert data['skills'][0]['status'] == "failed"
        assert data['version'] == 3, "Version should increment"
        print("✓ Updates existing skills")
        
        # Test 4: Log failure
        memory.log_failure("test_skill", "Test error", "code snippet")
        data = memory.read()
        assert len(data['failures']) == 1, "Should have 1 failure"
        assert data['failures'][0]['error'] == "Test error"
        print("✓ Logs failures")
        
        # Test 5: Add directive
        idx = memory.add_directive("Test goal")
        data = memory.read()
        assert len(data['directives']) == 1, "Should have 1 directive"
        assert data['directives'][0]['status'] == "pending"
        print("✓ Adds directives")
        
        # Test 6: Complete directive
        memory.complete_directive(idx)
        data = memory.read()
        assert data['directives'][0]['status'] == "completed"
        print("✓ Completes directives")
        
        # Test 7: Get relevant failures
        memory.log_failure("test_skill", "Error 2", "code 2")
        memory.log_failure("other_skill", "Error 3", "code 3")
        failures = memory.get_relevant_failures("test_skill")
        assert len(failures) == 2, "Should get skill-specific failures"
        print("✓ Retrieves relevant failures")
        
        # Test 8: Persistence across instances
        memory2 = PersistentMemory(temp_path)
        data2 = memory2.read()
        assert data2['version'] == data['version'], "Should persist across instances"
        assert len(data2['skills']) == len(data['skills'])
        print("✓ Persists across instances")
        
        print("\n✅ Persistent Memory: ALL TESTS PASSED")
    
    finally:
        # Cleanup
        temp_path.unlink(missing_ok=True)


def test_python_executor():
    """Test Python execution sandbox."""
    print("\n" + "="*70)
    print("TEST: Python Executor")
    print("="*70)
    
    executor = PythonExecutor(WORKSPACE_ROOT, timeout=5)
    
    # Test 1: Successful execution
    code = """
print("Hello, World!")
result = 2 + 2
print(f"Result: {result}")
    """
    result = executor.execute(code, "test")
    assert result['success'], "Should execute successfully"
    assert "Hello, World!" in result['stdout']
    assert "Result: 4" in result['stdout']
    print("✓ Executes valid code")
    
    # Test 2: Syntax error
    code = "print('Missing closing quote"
    result = executor.execute(code, "test")
    assert not result['success'], "Should fail on syntax error"
    assert "SyntaxError" in result['stderr'] or "unterminated" in result['stderr']
    print("✓ Catches syntax errors")
    
    # Test 3: Runtime error
    code = "x = 1 / 0"
    result = executor.execute(code, "test")
    assert not result['success'], "Should fail on runtime error"
    assert "ZeroDivisionError" in result['stderr']
    print("✓ Catches runtime errors")
    
    # Test 4: Timeout
    code = """
import time
time.sleep(10)
print("This should not print")
    """
    result = executor.execute(code, "test")
    assert not result['success'], "Should timeout"
    assert "timeout" in result['stderr'].lower()
    print("✓ Enforces timeout")
    
    # Test 5: Output capture
    code = """
import sys
print("stdout message")
sys.stderr.write("stderr message\\n")
    """
    result = executor.execute(code, "test")
    assert "stdout message" in result['stdout']
    assert "stderr message" in result['stderr']
    print("✓ Captures stdout/stderr")
    
    print("\n✅ Python Executor: ALL TESTS PASSED")


def test_workspace_isolation():
    """Test workspace isolation verification."""
    print("\n" + "="*70)
    print("TEST: Workspace Isolation")
    print("="*70)
    
    # Test 1: Workspace is within CWD
    cwd = Path.cwd().resolve()
    workspace = WORKSPACE_ROOT
    assert str(workspace).startswith(str(cwd)), \
        f"Workspace {workspace} must be within {cwd}"
    print(f"✓ Workspace isolated: {workspace}")
    
    # Test 2: Required directories exist
    assert (workspace / "skills").exists(), "skills/ should exist"
    assert (workspace / "exec").exists(), "exec/ should exist"
    print("✓ Required directories exist")
    
    # Test 3: Memory file is accessible
    memory_file = workspace / "memory.json"
    assert memory_file.parent == workspace, "Memory file in workspace"
    print("✓ Memory file in workspace")
    
    print("\n✅ Workspace Isolation: ALL TESTS PASSED")


def test_dangerous_patterns():
    """Test dangerous pattern detection."""
    print("\n" + "="*70)
    print("TEST: Dangerous Pattern Detection")
    print("="*70)
    
    test_cases = [
        ("eval('1+1')", True, "eval"),
        ("exec('print(1)')", True, "exec"),
        ("os.system('ls')", True, "os.system"),
        ("subprocess.Popen(['ls'])", True, "subprocess.Popen"),
        ("__import__('os')", True, "__import__"),
        ("compile('1+1', '<string>', 'eval')", True, "compile"),
        ("print('hello')", False, "safe print"),
        ("x = 5 * 5", False, "safe math"),
        ("def factorial(n): return 1 if n <= 1 else n * factorial(n-1)", False, "safe recursion"),
    ]
    
    import re
    
    passed = 0
    for code, should_detect, description in test_cases:
        detected = False
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                detected = True
                break
        
        if detected == should_detect:
            status = "✓"
            passed += 1
        else:
            status = "✗"
        
        expected = "BLOCKED" if should_detect else "ALLOWED"
        actual = "BLOCKED" if detected else "ALLOWED"
        print(f"{status} {description}: {expected} (got {actual})")
    
    assert passed == len(test_cases), f"Only {passed}/{len(test_cases)} passed"
    print(f"\n✅ Dangerous Patterns: {passed}/{len(test_cases)} TESTS PASSED")


def run_all_tests():
    """Run all test suites."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   AUTONOMOUS AGENT - TEST SUITE                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        ("Workspace Isolation", test_workspace_isolation),
        ("Safety Enforcer", test_safety_enforcer),
        ("Persistent Memory", test_persistent_memory),
        ("Python Executor", test_python_executor),
        ("Dangerous Patterns", test_dangerous_patterns),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {name} ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
