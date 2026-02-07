# Autonomous Self-Improving Agent Setup Guide

## System Requirements
- **OS**: Ubuntu 24.04 LTS
- **Python**: 3.11+
- **Memory**: 4GB+ RAM recommended
- **Disk**: 10GB+ free space (for Ollama models)

## Installation

### 1. Install Ollama Server
```bash
# Install Ollama
curl https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama  # Auto-start on boot

# Pull the required model (choose one)
ollama pull qwen3-coder        # Default: Best for code generation (32K context)
# OR
ollama pull glm-4.7-flash      # Alternative: Faster, lighter (8K context)

# Verify installation
ollama list
```

### 2. Install Python Dependencies
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import langgraph; print(f'LangGraph: {langgraph.__version__}')"
python3 -c "import ollama; print(f'Ollama: {ollama.__version__}')"
```

### 3. Initialize Workspace
```bash
# Create workspace structure
mkdir -p agent_workspace/{skills,exec}

# Verify setup
python3 autonomous_agent.py
```

## Usage

### Interactive Mode
```bash
python3 autonomous_agent.py
```

Commands:
- `:directive <goal>` - Give the agent a new goal
- `:memory` - View persistent memory state
- `:skills` - List all learned skills
- `:quit` - Exit

### Example Session
```
Agent> :directive Create a JSON validator skill

🧠 PLANNING: Create a JSON validator skill
📝 WRITING: create_a_json_validator_skill.py
🧪 TESTING: create_a_json_validator_skill
✓ Test passed
🔍 ANALYZING: Results
✅ SUCCESS: Skill is working!

Agent> :skills
Skills (1):
  ✅ create_a_json_validator_skill: Create a JSON validator skill
```

## Architecture Overview

### Tiered Autonomy System

#### ✅ AUTO-APPROVED (No human intervention)
- Write `.py` files to `./agent_workspace/skills/`
- Execute Python code from workspace (15s timeout)
- Read/write within `./agent_workspace/` only

#### ⚠️ REQUIRES APPROVAL
- File operations outside workspace
- Network access (`curl`, `requests`, etc.)
- System commands (`rm`, `sudo`, shell execution)

### Safety Enforcement
1. **Path Traversal Protection**: Blocks `..` and absolute paths
2. **Code Pattern Detection**: Blocks dangerous patterns:
   - `eval()`, `exec()`
   - `os.system()`, `subprocess.Popen()`
   - `__import__()`, `compile()`
   - Uncontrolled `open()` for writing
3. **Execution Timeout**: 15 seconds maximum
4. **Workspace Isolation**: All operations confined to `./agent_workspace/`

### Self-Improvement Loop

```
┌─────────────────────────────────────────────┐
│ 1. Receive Goal                             │
│    "Create a CSV parser skill"              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 2. PLAN: Generate skill code                │
│    - Review past failures                   │
│    - Use LLM to write code                  │
│    - Safety check                           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 3. WRITE: Save to skills/csv_parser.py      │
│    - Auto-approved (workspace operation)    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 4. TEST: Execute with harness               │
│    - Sandboxed execution                    │
│    - 15s timeout                            │
│    - Capture stdout/stderr                  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ 5. ANALYZE: Check results                   │
│    - Use LLM to evaluate output             │
│    - Detect failures                        │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
    ✅ SUCCESS          ❌ FAILURE
    Update memory      Log to memory
         │                   │
         │                   ▼
         │              Iteration < 12?
         │                   │
         │              ┌────┴────┐
         │              ▼         ▼
         │             Yes        No
         │              │         │
         │              └─────┐   │
         │                    │   ▼
         │                    │  FAILED
         │                    │  Mark skill
         │                    ▼
         └──────────────> GOTO 2 (Retry)
```

## Memory Structure

### memory.json Format
```json
{
  "version": 1,
  "skills": [
    {
      "name": "json_validator",
      "status": "working",
      "description": "Validates JSON strings",
      "created_at": "2026-02-07T10:30:00",
      "updated_at": "2026-02-07T10:35:00"
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
      "goal": "Create a CSV to JSON converter",
      "status": "pending",
      "created_at": "2026-02-07T10:40:00"
    }
  ]
}
```

### Skill Status
- `working` - Successfully tested and functional
- `untested` - Created but not yet validated
- `failed` - Unable to create working version after max iterations

## Workspace Structure

```
agent_workspace/
├── memory.json              # Persistent memory (survives restarts)
├── skills/                  # Generated skill modules
│   ├── json_validator.py
│   ├── csv_parser.py
│   └── xml_processor.py
└── exec/                    # Temporary execution files (auto-cleaned)
    └── (transient files)
```

## Configuration

Edit these constants in `autonomous_agent.py`:

```python
WORKSPACE_ROOT = Path("./agent_workspace").resolve()
OLLAMA_MODEL = "qwen3-coder"
MAX_ITERATIONS = 12           # Max retries per skill
EXECUTION_TIMEOUT = 15        # Seconds
```

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
systemctl status ollama

# Start manually if needed
sudo systemctl start ollama

# Test connection
ollama list
curl http://localhost:11434/api/tags
```

### Dependency Conflicts
```bash
# Clean reinstall
pip uninstall -y langgraph langchain-ollama ollama
pip install --no-cache-dir -r requirements.txt

# Verify versions
pip list | grep -E "langgraph|ollama|langchain"
# Expected:
# langgraph        0.3.x
# langchain-ollama 0.2.x or higher
# ollama           0.5.x or higher
```

### Permission Issues
```bash
# Ensure workspace is writable
chmod -R u+w agent_workspace/

# Check workspace isolation
python3 -c "from pathlib import Path; print(Path('./agent_workspace').resolve())"
```

### Model Not Found
```bash
# Pull model explicitly
ollama pull qwen3-coder         # Default option
# OR
ollama pull glm-4.7-flash       # Faster alternative

# List available models
ollama list

# Try alternative model (edit autonomous_agent.py)
# OLLAMA_MODEL = "glm-4.7-flash"  # Uncomment and change as needed
```

## Advanced Usage

### Programmatic API
```python
from autonomous_agent import AutonomousAgent

# Initialize
agent = AutonomousAgent()

# Run with custom goal
agent.run(
    goal="Create a regex pattern matcher",
    skill_name="regex_matcher"
)

# Access memory
memory = agent.memory.read()
print(f"Total skills: {len(memory['skills'])}")
```

### Batch Processing
```python
goals = [
    "Create a base64 encoder",
    "Create a URL parser",
    "Create a markdown to HTML converter"
]

agent = AutonomousAgent()
for goal in goals:
    agent.run(goal)
```

### Custom Safety Rules
```python
# Add to DANGEROUS_PATTERNS in autonomous_agent.py
DANGEROUS_PATTERNS.append(r"\brequests\.get\s*\(")  # Block network calls
```

## Performance Notes

- **First run**: May take 2-3 minutes (model loading)
- **Subsequent runs**: ~30-60 seconds per skill
- **Memory usage**: ~2-4GB (model + Python runtime)
- **Disk usage**: ~5GB (Ollama model) + workspace

## Safety Guarantees

1. ✅ **Workspace Isolation**: All file operations verified to be within workspace
2. ✅ **Code Sandboxing**: Dangerous patterns blocked before execution
3. ✅ **Execution Timeout**: All code runs have 15s hard limit
4. ✅ **Environment Restriction**: Python runs with minimal PYTHONPATH
5. ✅ **Path Traversal Protection**: `..` and absolute paths rejected

## Limitations

- **No network access**: Skills cannot make HTTP requests (by design)
- **No system commands**: Cannot execute shell commands
- **Single-file skills**: Each skill must be self-contained
- **15s timeout**: Long-running operations will be killed
- **Local models only**: Requires Ollama server on localhost

## Future Enhancements

- [ ] Multi-file skill support
- [ ] Skill dependency management
- [ ] Human approval workflow for system operations
- [ ] Skill version control
- [ ] Performance metrics tracking
- [ ] Remote model support (OpenAI, Anthropic)
- [ ] Parallel skill development

## License

MIT License - See LICENSE file

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review memory.json for failure logs
3. Examine agent_workspace/skills/ for generated code
4. Enable debug logging in autonomous_agent.py
