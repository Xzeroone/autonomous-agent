# Autonomous Self-Improving Agent

Production-ready autonomous agent built with **LangGraph** + **Ollama** for Ubuntu 24.04. Features tiered autonomy, persistent memory, and self-improvement through iterative skill development.

## 🎯 Key Features

- **🤖 Full Autonomy**: Operates independently within workspace (no human approval needed)
- **🛡️ Tiered Safety**: Requires approval for system-level operations
- **🧠 Persistent Memory**: OpenCLAW-style JSON memory survives restarts
- **🔄 Self-Improvement Loop**: Learns from failures, iterates until success
- **🏗️ LangGraph 0.3.x**: State machine with proper START/END handling
- **⚡ Ollama-Powered**: Local LLM inference with qwen3-coder or glm-4.7-flash

## 🚀 Quick Start

```bash
# 1. Clone/download the files
cd autonomous-agent/

# 2. Run automated setup
./setup.sh

# 3. Activate environment
source venv/bin/activate

# 4. Start the agent
python3 autonomous_agent.py
```

> **Note**: The default model is `qwen3-coder`. For faster performance or limited resources, see [MODEL_GUIDE.md](MODEL_GUIDE.md) to switch to `glm-4.7-flash`.

## 📋 Prerequisites

- **OS**: Ubuntu 24.04 LTS
- **Python**: 3.11+
- **RAM**: 4GB+ recommended
- **Disk**: 10GB+ free space

## 🎮 Usage Examples

### Interactive Mode
```bash
$ python3 autonomous_agent.py

Agent> :directive Create a JSON validator skill
🧠 PLANNING: Create a JSON validator skill
📝 WRITING: json_validator.py
🧪 TESTING: json_validator
✅ SUCCESS: Skill json_validator is working!

Agent> :skills
Skills (1):
  ✅ json_validator: Create a JSON validator skill

Agent> :memory
{
  "version": 2,
  "skills": [...],
  "failures": [],
  "directives": [...]
}
```

### Programmatic Usage
```python
from autonomous_agent import AutonomousAgent

agent = AutonomousAgent()
agent.run(
    goal="Create a CSV to JSON converter",
    skill_name="csv_converter"
)
```

### Batch Processing
```python
goals = [
    "Create a base64 encoder",
    "Create a regex pattern matcher",
    "Create a URL parser"
]

agent = AutonomousAgent()
for goal in goals:
    agent.run(goal)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  START ──▶ PLAN ──▶ WRITE ──▶ TEST ──▶ ANALYZE        │
│              │                              │            │
│              │                              ▼            │
│              │                          SUCCESS?         │
│              │                         ╱        ╲       │
│              │                       YES        NO       │
│              │                        │          │       │
│              │                        ▼          │       │
│              │                      END    Iter < 12?   │
│              │                              ╱    ╲     │
│              │                            YES    NO     │
│              │                             │      │     │
│              └─────────────────────────────┘      ▼     │
│                                                  END     │
└─────────────────────────────────────────────────────────┘

                    ▼ INTERACTS WITH ▼

┌─────────────────────────────────────────────────────────┐
│                   CORE COMPONENTS                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐  ┌──────────────────┐            │
│  │ Persistent      │  │ Safety           │            │
│  │ Memory          │  │ Enforcer         │            │
│  │ (memory.json)   │  │ (Tiered Autonomy)│            │
│  └─────────────────┘  └──────────────────┘            │
│                                                          │
│  ┌─────────────────┐  ┌──────────────────┐            │
│  │ Python          │  │ Ollama LLM       │            │
│  │ Executor        │  │ (qwen3-coder)    │            │
│  │ (Sandboxed)     │  │                  │            │
│  └─────────────────┘  └──────────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────┘

                    ▼ OPERATES IN ▼

┌─────────────────────────────────────────────────────────┐
│                ISOLATED WORKSPACE                        │
├─────────────────────────────────────────────────────────┤
│  agent_workspace/                                        │
│  ├── memory.json         (persistent state)             │
│  ├── skills/             (generated .py files)          │
│  │   ├── json_validator.py                             │
│  │   ├── csv_parser.py                                 │
│  │   └── ...                                            │
│  └── exec/               (temp execution, auto-clean)   │
└─────────────────────────────────────────────────────────┘
```

## 🔒 Safety System

### Tiered Autonomy

#### ✅ **AUTO-APPROVED** (No human intervention)
- Write `.py` files to `./agent_workspace/skills/`
- Execute Python code from workspace (15s timeout)
- Read/write within `./agent_workspace/` only

#### ⚠️ **REQUIRES APPROVAL**
- File operations outside workspace
- Network access (`curl`, `requests`)
- System commands (`rm`, `sudo`, shell execution)

### Safety Enforcement
1. **Path Traversal Protection**: Blocks `..` and absolute paths
2. **Code Pattern Detection**: Blocks:
   - `eval()`, `exec()`
   - `os.system()`, `subprocess.Popen()`
   - `__import__()`, `compile()`
   - Uncontrolled file writes
3. **Execution Timeout**: 15 seconds hard limit
4. **Workspace Isolation**: All operations verified within workspace

## 🧠 Memory System

### Structure (memory.json)
```json
{
  "version": 1,
  "skills": [
    {
      "name": "json_validator",
      "status": "working",
      "description": "Validates JSON strings",
      "created_at": "2026-02-07T10:30:00"
    }
  ],
  "failures": [
    {
      "skill": "json_validator",
      "error": "JSONDecodeError: Expecting value",
      "code_snippet": "json.loads(data)...",
      "timestamp": "2026-02-07T10:32:00"
    }
  ],
  "directives": [
    {
      "goal": "Create CSV to JSON converter",
      "status": "pending",
      "created_at": "2026-02-07T10:40:00"
    }
  ]
}
```

### Skill Status
- `working` - Tested and functional
- `untested` - Created but not validated
- `failed` - Max iterations reached without success

## 🔧 Configuration

Edit constants in `autonomous_agent.py`:

```python
WORKSPACE_ROOT = Path("./agent_workspace").resolve()
OLLAMA_MODEL = "qwen3-coder"      # Or "glm-4.7-flash"
MAX_ITERATIONS = 12               # Max retries per skill
EXECUTION_TIMEOUT = 15            # Seconds
```

### Supported Models
- **qwen3-coder** (default): Optimized for code generation, 32K context
- **glm-4.7-flash**: Fast and efficient, 8K context, good for simpler tasks

## 🧪 Testing

```bash
# Run comprehensive test suite
python3 test_agent.py

# Run example demos
python3 example_usage.py
```

## 📊 Performance

- **First run**: 2-3 minutes (model loading)
- **Subsequent runs**: 30-60 seconds per skill
- **Memory usage**: 2-4GB (model + runtime)
- **Disk usage**: ~5GB (Ollama model) + workspace

## 🔍 Troubleshooting

### Dependency Conflicts
```bash
# Clean reinstall with correct versions
pip uninstall -y langgraph langchain-ollama ollama
pip install --no-cache-dir -r requirements.txt
```

### Ollama not running
```bash
sudo systemctl start ollama
ollama pull qwen3-coder
```

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 📁 Project Structure

```
autonomous-agent/
├── autonomous_agent.py      # Main agent implementation
├── requirements.txt         # Python dependencies
├── setup.sh                 # Automated setup script
├── test_agent.py           # Test suite
├── example_usage.py        # Usage examples
├── SETUP_GUIDE.md          # Detailed documentation
├── MODEL_GUIDE.md          # Model comparison & selection
├── README.md               # This file
└── agent_workspace/        # Agent workspace (created on first run)
    ├── memory.json
    ├── skills/
    └── exec/
```

## 🎯 Use Cases

1. **Rapid Prototyping**: Generate utility functions on-demand
2. **Code Learning**: Watch the agent iterate and improve
3. **Testing Automation**: Create test harnesses automatically
4. **Data Processing**: Build custom parsers and validators
5. **Educational Tool**: Study LLM-based code generation

## ⚙️ Technical Stack

- **LangGraph 0.3.x**: State machine orchestration
- **Ollama**: Local LLM inference
- **qwen3-coder / glm-4.7-flash**: Code-specialized models
- **Python 3.11+**: Runtime environment
- **Ubuntu 24.04**: Target platform

## 🔐 Security Guarantees

1. ✅ **Workspace Isolation**: All file ops verified within workspace
2. ✅ **Code Sandboxing**: Dangerous patterns blocked pre-execution
3. ✅ **Execution Timeout**: 15s hard limit on all code
4. ✅ **Environment Restriction**: Minimal PYTHONPATH only
5. ✅ **Path Traversal Protection**: `..` and absolute paths rejected

## 🚧 Limitations

- **No network access**: Skills cannot make HTTP requests (by design)
- **No system commands**: Cannot execute shell commands
- **Single-file skills**: Each skill must be self-contained
- **15s timeout**: Long-running operations will be killed
- **Local only**: Requires Ollama server on localhost

## 🛣️ Roadmap

- [ ] Multi-file skill support
- [ ] Skill dependency management
- [ ] Interactive approval workflow for system ops
- [ ] Skill version control with git integration
- [ ] Performance metrics and analytics
- [ ] Remote model support (OpenAI, Anthropic)
- [ ] Parallel skill development
- [ ] Web UI dashboard

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📞 Support

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md) - 5-minute deployment
- **Model Selection**: [MODEL_GUIDE.md](MODEL_GUIDE.md) - Compare qwen3-coder vs glm-4.7-flash
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Fix dependency and installation issues
- **Setup Guide**: Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed installation
- **Logs**: Review `agent_workspace/memory.json` for failure history
- **Debug**: Examine generated code in `agent_workspace/skills/`

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [Ollama](https://ollama.com/)
- Inspired by OpenCLAW architecture
- Models: [Qwen3 Coder](https://ollama.com/library/qwen3-coder), [GLM-4.7-Flash](https://ollama.com/library/glm-4.7-flash)

## 📝 Citation

```bibtex
@software{autonomous_agent_2026,
  title = {Autonomous Self-Improving Agent},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/autonomous-agent}
}
```

---

**Built with ❤️ for autonomous AI development**
