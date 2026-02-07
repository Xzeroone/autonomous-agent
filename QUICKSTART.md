# ⚡ QUICK START DEPLOYMENT GUIDE

## 📦 What's Included

```
autonomous-agent/
├── autonomous_agent.py      ⭐ Main agent (23KB, 800+ lines)
├── requirements.txt         📋 Python dependencies
├── setup.sh                 🔧 Automated setup script
├── validate_setup.py        ✅ Pre-deployment validation
├── test_agent.py           🧪 Comprehensive test suite
├── example_usage.py        📚 Usage examples
├── config_example.py       ⚙️  Configuration template
├── README.md               📖 Main documentation
├── SETUP_GUIDE.md          📘 Detailed setup guide
├── LICENSE                 ⚖️  MIT License
└── .gitignore              🚫 Git ignore rules
```

## 🚀 3-Step Deployment (5 minutes)

### Step 1: Validate Environment
```bash
python3 validate_setup.py
```

Expected output:
```
✅ PASSED System Requirements
✅ PASSED Python Dependencies
✅ PASSED Ollama Model
✅ PASSED Workspace Structure
✅ PASSED File Permissions
```

### Step 2: Run Setup (if validation failed)
```bash
./setup.sh
```

This will:
- Install Ollama (if needed)
- Pull qwen3-coder model
- Create virtual environment
- Install Python dependencies
- Create workspace structure

### Step 3: Start Agent
```bash
source venv/bin/activate
python3 autonomous_agent.py
```

## 🎯 First Commands

```bash
# Try these in order:

Agent> :directive Create a function to reverse a string
# Watch it plan → write → test → analyze

Agent> :skills
# See your first skill

Agent> :memory
# View persistent memory

Agent> :directive Create a JSON validator
# Build a more complex skill
```

## ✅ Verification Steps

### 1. Check Ollama
```bash
ollama list
# Should show: qwen3-coder

curl http://localhost:11434/api/tags
# Should return JSON with models
```

### 2. Test Dependencies
```bash
python3 -c "import langgraph; print(langgraph.__version__)"
# Should print: 0.3.x

python3 -c "from langchain_ollama import ChatOllama; print('OK')"
# Should print: OK
```

### 3. Run Tests
```bash
python3 test_agent.py
# Should show: ALL TESTS PASSED
```

### 4. Try Examples
```bash
python3 example_usage.py
# Runs 5 demos automatically
```

## 🔍 Troubleshooting Quick Fixes

### ❌ "Ollama not found"
```bash
curl https://ollama.com/install.sh | sh
sudo systemctl start ollama
ollama pull qwen3-coder  # Or: ollama pull glm-4.7-flash
```

### ❌ "ImportError: langgraph"
```bash
pip install --no-cache-dir langgraph langchain-ollama ollama pydantic

# For detailed help: see TROUBLESHOOTING.md
```

### ❌ "Permission denied"
```bash
chmod +x setup.sh test_agent.py example_usage.py validate_setup.py
```

### ❌ "Model not found"
```bash
ollama pull qwen3-coder        # Default: Best for code
# OR
ollama pull glm-4.7-flash      # Alternative: Faster
# Wait 5-10 minutes for download
```

### ❌ "Connection refused"
```bash
sudo systemctl status ollama
# If not running:
sudo systemctl start ollama
```

## 📊 Success Indicators

After setup, you should see:

1. ✅ **Ollama**: `ollama list` shows qwen3-coder (or glm-4.7-flash)
2. ✅ **Python**: `python3 --version` shows 3.11+
3. ✅ **Dependencies**: All imports work without errors
4. ✅ **Workspace**: `agent_workspace/` directory exists
5. ✅ **Agent**: CLI starts with welcome banner

## 🎓 Next Steps

1. **Read the docs**: [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed info
2. **Run examples**: `python3 example_usage.py` to see demos
3. **Run tests**: `python3 test_agent.py` to verify everything
4. **Customize**: Edit `config_example.py` and save as `config.py`
5. **Build skills**: Start with simple goals and iterate

## 🔥 Pro Tips

- Start with simple skills to learn the system
- Check `agent_workspace/skills/` to see generated code
- Use `:memory` to debug failures
- Each skill is self-contained Python code
- The agent learns from failures automatically
- Memory persists across restarts

## 🆘 Getting Help

1. **Validation fails**: Run `validate_setup.py` for diagnostics
2. **Dependency issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed fixes
3. **Tests fail**: Run `python3 test_agent.py -v` for details
4. **Agent errors**: Check `agent_workspace/memory.json` for logs
5. **Skill bugs**: Examine `agent_workspace/skills/*.py`

## ⚡ Speed Run (For Experts)

```bash
# Complete setup in one command:
./setup.sh && source venv/bin/activate && python3 autonomous_agent.py
```

## 🎉 You're Ready!

Once validation passes, you have a fully functional autonomous agent that can:
- ✅ Write Python skills automatically
- ✅ Test and iterate on failures
- ✅ Learn from mistakes
- ✅ Operate safely in isolated workspace
- ✅ Persist memory across sessions

**Time to deployment**: ~5 minutes (including model download)

---

**Need more details?** See [SETUP_GUIDE.md](SETUP_GUIDE.md)
**Want examples?** Run `python3 example_usage.py`
**Have issues?** Run `python3 validate_setup.py`
