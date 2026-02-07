#!/usr/bin/env python3
"""
Pre-deployment validation script.
Checks all requirements before running the agent.
"""

import subprocess
import sys
from pathlib import Path


def check_system():
    """Check system requirements."""
    print("="*70)
    print("SYSTEM REQUIREMENTS CHECK")
    print("="*70)
    
    checks = []
    
    # Python version
    version_info = sys.version_info
    version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    python_ok = version_info.major == 3 and version_info.minor >= 11
    checks.append(("Python 3.11+", version, python_ok))
    
    # Ubuntu version (best effort)
    try:
        with open("/etc/os-release") as f:
            os_info = f.read()
            ubuntu_ok = "24.04" in os_info or "Ubuntu" in os_info
            os_version = "Ubuntu 24.04" if ubuntu_ok else "Unknown"
    except:
        ubuntu_ok = False
        os_version = "Cannot detect"
    checks.append(("Ubuntu 24.04", os_version, ubuntu_ok))
    
    # Ollama installation
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        ollama_ok = result.returncode == 0
        ollama_version = result.stdout.strip() if ollama_ok else "Not installed"
    except:
        ollama_ok = False
        ollama_version = "Not found"
    checks.append(("Ollama", ollama_version, ollama_ok))
    
    # Print results
    for name, value, ok in checks:
        status = "✅" if ok else "❌"
        print(f"{status} {name:20s}: {value}")
    
    return all(ok for _, _, ok in checks)


def check_dependencies():
    """Check Python dependencies."""
    print("\n" + "="*70)
    print("PYTHON DEPENDENCIES CHECK")
    print("="*70)
    
    required = {
        "langgraph": "0.3.0",
        "langchain-ollama": "0.2.0",
        "ollama": "0.5.3",
        "pydantic": "2.5.0",
    }
    
    checks = []
    for package, min_version in required.items():
        try:
            result = subprocess.run(
                ["pip", "show", package],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        installed = line.split(":")[1].strip()
                        ok = True
                        checks.append((package, installed, ok))
                        break
            else:
                checks.append((package, "Not installed", False))
        except:
            checks.append((package, "Error checking", False))
    
    for name, version, ok in checks:
        status = "✅" if ok else "❌"
        print(f"{status} {name:20s}: {version}")
    
    return all(ok for _, _, ok in checks)


def check_ollama_model():
    """Check if required model is available."""
    print("\n" + "="*70)
    print("OLLAMA MODEL CHECK")
    print("="*70)
    
    required_model = "qwen3-coder"  # Alternative: "glm-4.7-flash"
    
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            if required_model in result.stdout:
                print(f"✅ {required_model}: Available")
                return True
            else:
                print(f"❌ {required_model}: Not found")
                print(f"\nRun: ollama pull {required_model}")
                return False
        else:
            print(f"❌ Ollama service not running")
            print("\nRun: sudo systemctl start ollama")
            return False
    except:
        print(f"❌ Cannot connect to Ollama")
        return False


def check_workspace():
    """Check workspace structure."""
    print("\n" + "="*70)
    print("WORKSPACE CHECK")
    print("="*70)
    
    workspace = Path("./agent_workspace")
    
    checks = [
        (workspace, "Workspace root"),
        (workspace / "skills", "Skills directory"),
        (workspace / "exec", "Execution directory"),
    ]
    
    all_ok = True
    for path, description in checks:
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {description:20s}: {path}")
        
        if not exists:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"   └─ Created")
            except Exception as e:
                print(f"   └─ Error: {e}")
                all_ok = False
    
    return all_ok


def check_permissions():
    """Check file permissions."""
    print("\n" + "="*70)
    print("PERMISSIONS CHECK")
    print("="*70)
    
    files = [
        "autonomous_agent.py",
        "setup.sh",
        "test_agent.py",
        "example_usage.py",
    ]
    
    all_ok = True
    for filename in files:
        path = Path(filename)
        if path.exists():
            is_executable = path.stat().st_mode & 0o111
            status = "✅" if is_executable else "⚠️"
            print(f"{status} {filename:25s}: {'Executable' if is_executable else 'Not executable'}")
        else:
            print(f"❌ {filename:25s}: Not found")
            all_ok = False
    
    return all_ok


def main():
    """Run all checks."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   AUTONOMOUS AGENT - PRE-DEPLOYMENT VALIDATION                ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    checks = [
        ("System Requirements", check_system),
        ("Python Dependencies", check_dependencies),
        ("Ollama Model", check_ollama_model),
        ("Workspace Structure", check_workspace),
        ("File Permissions", check_permissions),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name} check failed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:12s} {name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n✅ ALL CHECKS PASSED - Ready to deploy!")
        print("\nNext steps:")
        print("  1. source venv/bin/activate")
        print("  2. python3 autonomous_agent.py")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED - Please fix issues above")
        print("\nCommon fixes:")
        print("  • Install Ollama: curl https://ollama.com/install.sh | sh")
        print("  • Install deps: pip install -r requirements.txt")
        print("  • Pull model: ollama pull qwen3-coder-next")
        print("  • Fix permissions: chmod +x *.sh *.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
