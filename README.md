# Autonomous Self-Improving Agent

Production-ready autonomous agent built with **Ollama** for Ubuntu 24.04. Features **LLM-driven autonomy**, tiered safety, persistent memory, self-improvement through iterative skill development, **framework registry**, **tool classification**, and **DIRECT_ANSWER capability**.

## 🎯 Key Features

- **🧠 LLM as Brain**: LLM decides all actions dynamically (llm-central mode, default)
- **📊 LangGraph as Tool**: Graph-based workflow coordination available when needed
- **🔄 Dual Modes**: Switch between LLM-central (autonomous) and graph (structured) modes
- **🛡️ Tiered Safety**: Requires approval for system-level operations
- **🧠 Persistent Memory**: OpenCLAW-style JSON memory survives restarts
- **🔄 Self-Improvement Loop**: Learns from failures, iterates until success
- **⚡ Ollama-Powered**: Local LLM inference with qwen3-coder or glm-4.7-flash
- **🔧 Framework Registry**: Reusable code generation components (NEW)
- **🏷️ Tool Classification**: THINK vs DO tool organization (NEW)
- **💬 DIRECT_ANSWER**: LLM can respond without invoking tools (NEW)
- **🕸️ Dynamic Planner**: LangGraph-based dynamic workflow execution (NEW)

## 🏗️ Architecture Philosophy

### The Agent as an Organism

This agent is designed with a biological metaphor:

- **🧠 LLM = Brain**: The central controller that makes all decisions, evaluates context, and chooses actions
- **🕸️ LangGraph = Nervous System**: Coordination system the brain can use when structured workflows are needed
- **🔧 Tools = Body Parts**: Extensible tools (plan, write, test, analyze, memory) the brain controls
- **🛡️ Safety System = Immune System**: Protects against harmful operations
- **💾 Memory = Long-term Storage**: Persistent knowledge that survives restarts

### Two Operating Modes

#### 1. LLM-Central Mode (Default) - **Autonomous Brain**
```
┌─────────────────────────────────────────────────────────┐
│                      LLM BRAIN                           │
│              (Decision-Making Controller)                │
└─────────────────┬───────────────────────────────────────┘
                  │ Evaluates context, decides actions
                  ▼
    ┌─────────────────────────────────────────────┐
    │         AVAILABLE TOOLS                      │
    ├─────────────────────────────────────────────┤
    │  • plan_skill    - Generate code            │
    │  • write_skill   - Save to file             │
    │  • test_skill    - Execute & validate       │
    │  • analyze_results - Evaluate success       │
    │  • memory_ops    - Read/write memory        │
    │  • LangGraph     - Structured coordination  │
    └─────────────────────────────────────────────┘

Flow: LLM → Decide → Tool → Result → LLM → Decide → ...
```

The LLM receives the goal, current state, and available tools, then decides what to do next. It can:
- Plan and generate code
- Write skills to files
- Test code execution
- Analyze results
- Manage memory
- Even invoke LangGraph for structured sub-workflows if needed

#### 2. Graph Mode (Legacy) - **Structured Workflow**
```
┌─────────────────────────────────────────────────────────┐
│                   LANGGRAPH WORKFLOW                     │
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

Flow: Fixed graph path with conditional loops
```

Fixed workflow orchestrated by LangGraph. Each step is predetermined, but the LLM is invoked within each node for specific tasks.

## 🚀 Quick Start

```bash
# 1. Clone/download the files
cd autonomous-agent/

# 2. Run automated setup
./setup.sh

# 3. Activate environment
source venv/bin/activate

# 4. Start the agent (LLM-central mode by default)
python3 autonomous_agent.py

# OR use legacy graph mode
python3 autonomous_agent.py --graph
```

> **Note**: The default model is `qwen3-coder`. For faster performance or limited resources, see [MODEL_GUIDE.md](MODEL_GUIDE.md) to switch to `glm-4.7-flash`.

## 📋 Prerequisites

- **OS**: Ubuntu 24.04 LTS
- **Python**: 3.11+
- **RAM**: 4GB+ recommended
- **Disk**: 10GB+ free space

## 🎮 Usage Examples

### Interactive Mode (LLM-Central)
```bash
$ python3 autonomous_agent.py

Agent> :directive Create a JSON validator skill
🧠 LLM-CENTRAL MODE: LLM is the brain, deciding all actions
🔄 Iteration 1/12
──────────────────────────────────────────────────────────────────
💭 DECISION: Need to generate code for JSON validator
⚡ ACTION: plan_skill
🔧 Executing tool: plan_skill
✓ Generated code (542 chars)
...
✅ SUCCESS: Skill json_validator is working!

Agent> :skills
Skills (1):
  ✅ json_validator: Create a JSON validator skill

Agent> :mode graph       # Switch to graph mode
✓ Switched to graph mode

Agent> :directive Create a CSV parser
📊 GRAPH MODE: LangGraph orchestrates fixed workflow
🧠 PLANNING: Create a CSV parser
...
```

### Command-Line Mode Selection
```bash
# LLM-central mode (default)
python3 autonomous_agent.py

# Graph mode (legacy)
python3 autonomous_agent.py --graph

# Explicit mode selection
python3 autonomous_agent.py --mode llm-central
python3 autonomous_agent.py --mode graph
```

### Programmatic Usage
```python
from autonomous_agent import AutonomousAgent

# LLM-central mode (default)
agent = AutonomousAgent(mode="llm-central")
agent.run(
    goal="Create a CSV to JSON converter",
    skill_name="csv_converter"
)

# Graph mode (legacy)
agent_graph = AutonomousAgent(mode="graph")
agent_graph.run(
    goal="Create a base64 encoder",
    skill_name="base64_encoder"
)
```

### Batch Processing
```python
goals = [
    "Create a base64 encoder",
    "Create a regex pattern matcher",
    "Create a URL parser"
]

agent = AutonomousAgent(mode="llm-central")
for goal in goals:
    agent.run(goal)
```

## ⚙️ Configuration & Modes

### Agent Modes

Edit constants in `autonomous_agent.py`:

```python
WORKSPACE_ROOT = Path("./agent_workspace").resolve()
OLLAMA_MODEL = "qwen3-coder"      # Or "glm-4.7-flash"
MAX_ITERATIONS = 12               # Max retries per skill
EXECUTION_TIMEOUT = 15            # Seconds
AGENT_MODE = "llm-central"        # Options: "llm-central" or "graph"
```

### Mode Comparison

| Feature | LLM-Central Mode | Graph Mode |
|---------|-----------------|------------|
| **Decision Making** | LLM chooses all actions dynamically | Fixed workflow graph |
| **Flexibility** | High - can adapt flow based on context | Low - predetermined path |
| **Autonomy** | True autonomous reasoning | Structured automation |
| **When to Use** | Complex tasks, exploratory work | Well-defined workflows |
| **Performance** | Slightly more LLM calls | Fewer, more targeted LLM calls |
| **Innovation** | Can discover novel approaches | Follows proven path |

### Switching Modes

**Command Line:**
```bash
python3 autonomous_agent.py --llm-central  # Default
python3 autonomous_agent.py --graph        # Legacy mode
```

**Interactive:**
```bash
Agent> :mode llm-central
✓ Switched to llm-central mode
Agent> :mode graph
✓ Switched to graph mode
```

**Programmatic:**
```python
agent = AutonomousAgent(mode="llm-central")  # or "graph"
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

## 🔧 Framework Registry (NEW)

The Framework Registry provides a system for managing reusable code generation components and templates.

### What is a Framework?

A framework is a reusable code generation template with:
- **Name**: Unique identifier
- **Type**: "think" (planning/analysis) or "do" (execution/action)
- **Language**: Target programming language
- **Components**: Dictionary of template parts

### Default Frameworks

Three built-in frameworks are registered automatically:

1. **python_generator** (DO, Python)
   - Components: header, main_function, test_harness
   - Use case: Generate complete Python functions with tests

2. **analysis_prompt** (THINK, Natural Language)
   - Components: analysis_template
   - Use case: Structure analytical thinking tasks

3. **test_harness** (DO, Python)
   - Components: test_setup, test_method, test_runner
   - Use case: Generate unittest-based test suites

### Using the Framework Registry

```python
from frameworks import FrameworkRegistry, register_default_frameworks

# Initialize and register defaults
registry = FrameworkRegistry()
register_default_frameworks(registry)

# List all frameworks
print(registry.list_frameworks())
# Output: ['python_generator', 'analysis_prompt', 'test_harness']

# Get frameworks by type
think_frameworks = registry.find_by_type("think")
do_frameworks = registry.find_by_type("do")

# Get frameworks by language
python_frameworks = registry.find_by_language("python")
```

### Tool Assembler

The ToolAssembler composes frameworks into deliverables with automatic safety checking:

```python
from frameworks import ToolAssembler

assembler = ToolAssembler(registry, safety_enforcer)

# Assemble a framework
result = assembler.assemble(
    frameworks=["python_generator"],
    params={
        "description": "A factorial calculator",
        "function_name": "factorial",
        "params": "n: int",
        "doc_string": "Calculate factorial of n",
        "test_params": "5"
    }
)

if result['success']:
    print(result['code'])  # Generated code
```

### PlanTool Framework Integration

PlanTool can now use frameworks instead of pure LLM generation:

```python
# Using frameworks
result = plan_tool.execute(
    goal="Create a factorial function",
    skill_name="factorial",
    frameworks=["python_generator"]  # Use framework instead of LLM
)

# Traditional LLM-based generation (fallback)
result = plan_tool.execute(
    goal="Create a factorial function",
    skill_name="factorial"
    # No frameworks = LLM generates from scratch
)
```

## 🏷️ Tool Classification (NEW)

Tools are classified into two types for better organization:

### THINK Tools (Planning & Analysis)
- **plan_skill**: Generate code plans
- **analyze_results**: Evaluate test outcomes
- **langgraph_planner**: Build dynamic workflows

### DO Tools (Execution & Action)
- **write_skill**: Save code to files
- **test_skill**: Execute and validate code
- **memory_ops**: Manage persistent memory

### Using Tool Classification

```python
agent = AutonomousAgent()

# Get all THINK tools
think_tools = agent.get_tools_by_type("think")
print(f"Planning tools: {list(think_tools.keys())}")

# Get all DO tools
do_tools = agent.get_tools_by_type("do")
print(f"Execution tools: {list(do_tools.keys())}")
```

## 💬 DIRECT_ANSWER Capability (NEW)

The LLM can now respond directly without invoking tools when appropriate.

### When DIRECT_ANSWER is Used

The LLM automatically chooses DIRECT_ANSWER for:
- Simple factual questions
- Conceptual explanations
- Quick clarifications
- Status inquiries

### Example Flow

```
User: "What is a decorator in Python?"

LLM Decision:
DECISION: This is a conceptual question I can answer directly
ACTION: DIRECT_ANSWER
PARAMS: {"response": "A decorator in Python is a design pattern..."}

Agent Output:
💬 DIRECT ANSWER: A decorator in Python is a design pattern that allows
you to modify or extend the behavior of functions or methods without
changing their source code...
```

### Traditional Tool-Based Flow

```
User: "Create a decorator for timing function execution"

LLM Decision:
DECISION: This requires code generation
ACTION: plan_skill
PARAMS: {"goal": "Create a timing decorator", "skill_name": "timer_decorator"}

Agent Output:
🔧 Executing tool: plan_skill
✓ Generated code (245 chars)
...
```

## 🕸️ LangGraph Dynamic Planner (NEW)

The `langgraph_planner` tool enables runtime creation of dynamic StateGraph workflows.

### Features
- Build workflows at runtime
- Define custom steps
- Sequential or conditional execution
- Automatic state management

### Example Usage

```python
# Use the langgraph_planner tool
result = agent.tools["langgraph_planner"].execute(
    steps=[
        {"name": "analyze", "handler": "analyze_task"},
        {"name": "plan", "handler": "create_plan"},
        {"name": "execute", "handler": "run_plan"}
    ],
    goal="Solve complex multi-step problem"
)

if result['success']:
    print(f"Workflow completed: {result['status']}")
    print(f"Steps executed: {len(result['results'])}")
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

### LLM-Central Mode (Best For)
1. **Complex Problem Solving**: Tasks requiring adaptive decision-making
2. **Exploratory Development**: When the solution approach is unclear
3. **Self-Directed Learning**: Agent discovers optimal workflow
4. **Research & Experimentation**: Testing novel approaches
5. **True Autonomy**: Minimal human intervention needed

### Graph Mode (Best For)
1. **Rapid Prototyping**: Generate utility functions on-demand
2. **Predictable Workflows**: When you know the exact steps needed
3. **Testing Automation**: Create test harnesses automatically
4. **Data Processing**: Build custom parsers and validators
5. **Educational Tool**: Study LLM-based code generation in structured flow

## ⚙️ Technical Stack

- **LLM Brain**: Primary decision-maker (LLM-central mode)
- **LangGraph 0.3.x**: Optional workflow orchestration tool
- **Ollama**: Local LLM inference
- **qwen3-coder / glm-4.7-flash**: Code-specialized models
- **Tool System**: Extensible architecture for adding capabilities
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

### Completed ✅
- [x] LLM-central mode (LLM as brain/decision-maker)
- [x] Tool system architecture
- [x] Backward compatibility (graph mode)
- [x] Mode switching (runtime + CLI)
- [x] Dynamic action selection by LLM

### Planned 🔮
- [ ] Additional tools (file operations, search, refactoring)
- [ ] LangGraph invocation as a tool (sub-workflow delegation)
- [ ] Multi-file skill support
- [ ] Skill dependency management
- [ ] Interactive approval workflow for system ops
- [ ] Skill version control with git integration
- [ ] Performance metrics and analytics
- [ ] Remote model support (OpenAI, Anthropic)
- [ ] Parallel skill development
- [ ] Web UI dashboard
- [ ] Meta-learning (agent improves its own decision-making)

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
