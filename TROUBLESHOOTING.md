# Dependency Troubleshooting Guide

## Common Installation Issues and Fixes

This guide covers dependency conflicts and installation problems you might encounter.

---

## ✅ Correct Dependency Versions

The agent requires these **compatible** versions:

```txt
langgraph>=0.3.0,<0.4.0
langchain-ollama>=0.2.0
ollama>=0.5.3
pydantic>=2.5.0,<3.0.0
watchdog==3.0.0
```

**Important**: `langchain-core` is auto-resolved by pip. Do NOT manually pin it.

---

## ❌ Problem 1: Ollama Version Conflict

### Error Message
```
ERROR: Cannot install -r requirements.txt (line 8) and ollama==0.3.3 
because these package versions have conflicting dependencies.

The conflict is caused by:
    langchain-ollama 0.3.8 depends on ollama<1.0.0 and >=0.5.3
```

### Root Cause
`langchain-ollama` requires `ollama>=0.5.3`, but an older version was specified.

### Solution
```bash
# 1. Clean existing installations
pip uninstall -y langgraph langchain-ollama ollama langchain-core

# 2. Clear pip cache
pip cache purge

# 3. Install from updated requirements.txt
pip install --no-cache-dir -r requirements.txt

# 4. Verify versions
pip list | grep -E "langgraph|ollama|langchain"
```

Expected output:
```
langgraph                0.3.x
langchain-core           0.3.x
langchain-ollama         0.2.x (or higher)
ollama                   0.5.x (or higher)
```

---

## ❌ Problem 2: LangGraph Import Error

### Error Message
```
ImportError: cannot import name 'START' from 'langgraph.graph'
```

### Root Cause
Using LangGraph < 0.3.0 which doesn't have START/END constants.

### Solution
```bash
# Upgrade to LangGraph 0.3.x
pip install --upgrade "langgraph>=0.3.0,<0.4.0"

# Verify
python3 -c "from langgraph.graph import START, END; print('OK')"
```

---

## ❌ Problem 3: langchain-core Conflict

### Error Message
```
ERROR: pip's dependency resolver does not currently take into account 
all the packages that are installed. This behaviour is the source of 
the following dependency conflicts.
```

### Root Cause
Manually pinned `langchain-core` version conflicts with other packages.

### Solution
```bash
# Let pip auto-resolve langchain-core
pip uninstall -y langchain-core
pip install --no-cache-dir langgraph langchain-ollama

# langchain-core will be installed automatically at compatible version
```

**Never specify `langchain-core` in requirements.txt**

---

## ❌ Problem 4: Virtual Environment Issues

### Error Message
```
ImportError: No module named 'langgraph'
```
(But pip shows it's installed)

### Root Cause
Wrong Python environment or multiple Python versions.

### Solution
```bash
# 1. Deactivate current environment
deactivate

# 2. Remove old venv
rm -rf venv/

# 3. Create fresh venv with Python 3.11+
python3.11 -m venv venv
# OR
python3 -m venv venv

# 4. Activate
source venv/bin/activate

# 5. Verify correct Python
which python3
python3 --version

# 6. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## ❌ Problem 5: SSL Certificate Errors

### Error Message
```
SSL: CERTIFICATE_VERIFY_FAILED
```

### Solution
```bash
# Option 1: Update CA certificates
sudo apt-get update
sudo apt-get install --reinstall ca-certificates

# Option 2: Use trusted host (not recommended for production)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

---

## ❌ Problem 6: Permission Denied

### Error Message
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/...'
```

### Root Cause
Trying to install system-wide without sudo, or pip is confused about location.

### Solution
```bash
# Always use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# If you must install system-wide (NOT recommended)
pip install --user -r requirements.txt
```

---

## ❌ Problem 7: Incompatible Python Version

### Error Message
```
ERROR: Package 'langgraph' requires a different Python: 3.8.x not in '>=3.11'
```

### Root Cause
Using Python < 3.11

### Solution
```bash
# Check Python version
python3 --version

# If < 3.11, install Python 3.11+
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Create venv with specific version
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ❌ Problem 8: Slow Installation

### Symptom
```
INFO: pip is looking at multiple versions... This could take a while.
```

### Cause
Pip is trying many version combinations to resolve dependencies.

### Solution
```bash
# 1. Use faster resolver (pip >= 20.3)
pip install --upgrade pip

# 2. Install in order (helps resolver)
pip install pydantic
pip install ollama
pip install langchain-ollama
pip install langgraph
pip install watchdog

# 3. OR use constraint file
pip install -r requirements.txt --no-deps
pip install langgraph langchain-ollama ollama pydantic watchdog
```

---

## ✅ Full Clean Reinstall (Nuclear Option)

If all else fails:

```bash
# 1. Deactivate and remove venv
deactivate 2>/dev/null || true
rm -rf venv/

# 2. Clear pip cache completely
pip cache purge
rm -rf ~/.cache/pip/

# 3. Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Upgrade pip and tools
pip install --upgrade pip setuptools wheel

# 5. Install dependencies one by one
pip install "pydantic>=2.5.0,<3.0.0"
pip install "ollama>=0.5.3"
pip install "langchain-ollama>=0.2.0"
pip install "langgraph>=0.3.0,<0.4.0"
pip install "watchdog==3.0.0"

# 6. Verify installation
python3 << 'EOF'
try:
    from langgraph.graph import START, END, StateGraph
    from langchain_ollama import ChatOllama
    import ollama
    import pydantic
    print("✅ All imports successful!")
    print(f"LangGraph: OK")
    print(f"Ollama: OK")
    print(f"Pydantic: OK")
except ImportError as e:
    print(f"❌ Import failed: {e}")
EOF
```

---

## 🧪 Testing Installation

After fixing dependencies:

```bash
# Test imports
python3 -c "from langgraph.graph import START, END; print('✅ LangGraph OK')"
python3 -c "from langchain_ollama import ChatOllama; print('✅ Ollama OK')"
python3 -c "import ollama; print('✅ Ollama client OK')"

# Test agent (dry run)
python3 -c "from autonomous_agent import PersistentMemory; print('✅ Agent imports OK')"

# Run full validation
python3 validate_setup.py
```

---

## 📋 Dependency Version Matrix

| Package | Min Version | Max Version | Notes |
|---------|-------------|-------------|-------|
| Python | 3.11.0 | 3.12.x | Ubuntu 24.04 has 3.12 |
| langgraph | 0.3.0 | <0.4.0 | Need START/END |
| langchain-ollama | 0.2.0 | latest | Auto-updated |
| ollama | 0.5.3 | <1.0.0 | Client library |
| pydantic | 2.5.0 | <3.0.0 | V2 API only |
| langchain-core | (auto) | (auto) | Let pip resolve |

---

## 🔍 Debugging Commands

```bash
# Check what's installed
pip list | grep -E "langgraph|ollama|langchain|pydantic"

# Check dependency tree
pip show langgraph
pip show langchain-ollama

# Check for conflicts
pip check

# See where packages are installed
pip show -f langgraph | grep Location

# Test in Python
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")
print(f"Path: {sys.executable}")

import langgraph
print(f"LangGraph: {langgraph.__version__}")

import ollama
print(f"Ollama: {ollama.__version__}")

from langgraph.graph import START, END
print("START/END constants available: OK")
EOF
```

---

## 🆘 Still Having Issues?

1. **Check Python version**: Must be 3.11+
   ```bash
   python3 --version
   ```

2. **Use virtual environment**: ALWAYS use venv
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Update pip**: Old pip versions have resolver bugs
   ```bash
   pip install --upgrade pip
   ```

4. **Check Ubuntu version**: Tested on 24.04
   ```bash
   cat /etc/os-release | grep VERSION
   ```

5. **Verify Ollama server** (separate from Python package):
   ```bash
   ollama --version
   sudo systemctl status ollama
   ```

6. **Run validation script**:
   ```bash
   python3 validate_setup.py
   ```

---

## 📞 Quick Reference

### Minimal Working Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install "langgraph>=0.3.0,<0.4.0" "langchain-ollama>=0.2.0" "ollama>=0.5.3" "pydantic>=2.5.0,<3.0.0"
```

### Verify Installation
```bash
python3 validate_setup.py
```

### Test Autonomous Agent
```bash
python3 test_agent.py
```

---

**Last Updated**: February 7, 2026  
**Tested On**: Ubuntu 24.04 LTS, Python 3.11+
