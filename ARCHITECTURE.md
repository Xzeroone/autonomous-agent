# Autonomous Agent Architecture

## Overview

This document describes the architectural refactoring that transforms the agent from a LangGraph-orchestrated system to an LLM-driven autonomous system.

## Design Philosophy: The Agent as an Organism

The agent is designed using a biological metaphor where different components work together like parts of a living organism:

### 🧠 LLM = Brain (Central Controller)
The LLM is the **brain** of the agent. It:
- Receives sensory input (current state, goal, history, available tools)
- Makes decisions about what to do next
- Selects which tools to use and when
- Adapts its strategy based on results
- Learns from failures through memory

**Key Insight**: The brain doesn't follow a predetermined path. It evaluates the situation and chooses the best action dynamically.

### 🕸️ LangGraph = Nervous System (Coordination Tool)
LangGraph is the **nervous system** - a coordination mechanism the brain can use when needed. It:
- Provides structured workflow execution when beneficial
- Available as a tool, not the master controller
- Can be invoked by the LLM for sub-workflows
- Optional - the LLM decides if/when to use it

**Key Insight**: The nervous system doesn't think; it carries out instructions from the brain.

### 🔧 Tools = Body Parts (Execution Mechanisms)
Tools are the **body parts** that execute actions:
- **PlanTool**: Generate code (like hands writing)
- **WriteTool**: Save files (like hands organizing)
- **TestTool**: Execute code (like legs moving)
- **AnalyzeTool**: Evaluate results (like eyes seeing)
- **MemoryTool**: Store/retrieve knowledge (like long-term memory)

**Key Insight**: Body parts don't decide what to do; they respond to brain commands.

### 🛡️ Safety System = Immune System (Protection)
The safety enforcer is the **immune system**:
- Detects dangerous patterns before execution
- Blocks harmful operations
- Maintains workspace isolation
- Protects against malicious code

**Key Insight**: The immune system works autonomously to protect the organism.

### 💾 Memory = Long-term Storage (Knowledge Base)
Persistent memory is **long-term storage**:
- Remembers skills learned
- Records failures to avoid
- Tracks directives and goals
- Survives restarts (file-based persistence)

**Key Insight**: Memory persists across sessions, enabling continuous learning.

## Architecture Comparison

### LLM-Central Mode (Default) - Autonomous

```
┌────────────────────────────────────────┐
│          LLM BRAIN (Controller)         │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ Decision Loop:                   │ │
│  │ 1. Evaluate context & goal       │ │
│  │ 2. Choose next action            │ │
│  │ 3. Select tool & parameters      │ │
│  │ 4. Process results               │ │
│  │ 5. Repeat until success/failure  │ │
│  └──────────────────────────────────┘ │
│                                        │
│          ↓ invokes ↓                   │
└────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
  ┌──────────┐        ┌──────────┐
  │  Tools   │        │LangGraph │
  │  - plan  │        │(Optional)│
  │  - write │        │          │
  │  - test  │        │          │
  │  - analyze│       │          │
  │  - memory│        │          │
  └──────────┘        └──────────┘
```

**Flow**: 
1. LLM receives goal + context
2. LLM decides "I need to generate code" → invokes PlanTool
3. LLM receives code → decides "I need to save it" → invokes WriteTool
4. LLM receives saved confirmation → decides "I need to test it" → invokes TestTool
5. LLM receives test results → decides "I need to analyze" → invokes AnalyzeTool
6. LLM receives analysis → decides COMPLETE or iterate

**Key Characteristics**:
- ✅ Dynamic flow - LLM chooses each step
- ✅ Can skip steps if not needed
- ✅ Can retry specific steps
- ✅ Can change strategy mid-task
- ✅ True autonomous reasoning

### Graph Mode (Legacy) - Structured

```
┌────────────────────────────────────────┐
│        LangGraph State Machine         │
│                                        │
│  START → PLAN → WRITE → TEST → ANALYZE│
│            ↑                      │    │
│            │          SUCCESS?    │    │
│            │          ↙      ↘    │    │
│            │        YES      NO   │    │
│            │         │        │   │    │
│            │         END  Iter<12?│    │
│            │                ↙   ↘ │    │
│            │              YES   NO│    │
│            └───────────────┘     END   │
│                                        │
│     Each node invokes LLM for         │
│     specific subtask                  │
└────────────────────────────────────────┘
```

**Flow**:
1. Graph starts at PLAN node
2. PLAN node invokes LLM to generate code
3. Graph transitions to WRITE node
4. WRITE node saves code
5. Graph transitions to TEST node
6. TEST node executes code
7. Graph transitions to ANALYZE node
8. ANALYZE node invokes LLM to evaluate
9. Graph decides SUCCESS or loop back to PLAN

**Key Characteristics**:
- ✅ Predictable flow - same path every time
- ✅ Easy to debug - fixed transitions
- ✅ Proven workflow - battle-tested
- ⚠️ Less flexible - can't adapt flow
- ⚠️ LLM is a tool, not the controller

## Decision-Making Process

### LLM-Central Mode

The LLM controller uses this prompt structure to make decisions:

```
Current Goal: <user's goal>
Current State: <what's been done so far>
Available Tools: <list of tools and descriptions>
Recent Actions: <last 5 actions and results>

Decide what to do next. Choose ONE tool or COMPLETE/FAILED.

Respond in this format:
DECISION: <your reasoning>
ACTION: <tool_name or COMPLETE or FAILED>
PARAMS: <JSON parameters for the tool>
```

Example decision sequence for "Create a factorial function":

**Iteration 1**:
```
DECISION: Need to generate Python code for factorial function
ACTION: plan_skill
PARAMS: {"goal": "Create a factorial function", "skill_name": "factorial", "iteration": 1}
```

**Iteration 2** (after successful code generation):
```
DECISION: Code generated successfully, now need to save it to file
ACTION: write_skill
PARAMS: {"skill_name": "factorial", "code": "<generated code>"}
```

**Iteration 3** (after successful write):
```
DECISION: File saved, now need to test if it works correctly
ACTION: test_skill
PARAMS: {"skill_name": "factorial", "code": "<generated code>"}
```

**Iteration 4** (after successful test):
```
DECISION: Test passed with correct output, need to analyze if requirements met
ACTION: analyze_results
PARAMS: {"skill_name": "factorial", "goal": "Create a factorial function", "test_result": "<output>"}
```

**Iteration 5** (after positive analysis):
```
DECISION: Analysis confirms function works correctly, goal achieved
ACTION: COMPLETE
PARAMS: {}
```

### Error Handling & Recovery

If a step fails, the LLM can:

1. **Retry with modifications**:
```
DECISION: Previous code had syntax error, regenerating with fix
ACTION: plan_skill
PARAMS: {"goal": "...", "skill_name": "...", "iteration": 3}
```

2. **Skip to different approach**:
```
DECISION: Direct approach failing, try generating simpler version first
ACTION: plan_skill
PARAMS: {"goal": "Create simple factorial without recursion", ...}
```

3. **Request more information**:
```
DECISION: Need to check what failed in previous attempts
ACTION: memory_ops
PARAMS: {"operation": "get_failures", "skill_name": "factorial"}
```

## Tool System

### Tool Interface

Each tool implements this interface:

```python
class AgentTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> dict:
        """
        Execute the tool and return result.
        
        Returns:
            {
                "success": bool,
                "message": str,
                # tool-specific fields
            }
        """
        raise NotImplementedError
```

### Available Tools

#### PlanTool
**Purpose**: Generate Python code based on goal

**Inputs**:
- `goal`: What the code should do
- `skill_name`: Name for the skill
- `iteration`: Current attempt number

**Outputs**:
- `success`: True if code generated safely
- `code`: Generated Python code
- `error`: Safety violation message if failed

**Safety**: Checks code for dangerous patterns before returning

#### WriteTool
**Purpose**: Save code to file in skills directory

**Inputs**:
- `skill_name`: Name of the skill
- `code`: Code to save

**Outputs**:
- `success`: True if file written
- `file_path`: Path to saved file
- `error`: Error message if failed

**Safety**: Ensures write happens within workspace

#### TestTool
**Purpose**: Execute code and capture results

**Inputs**:
- `skill_name`: Name being tested
- `code`: Code to execute

**Outputs**:
- `success`: True if execution succeeded
- `output`: stdout from execution
- `error`: stderr if failed

**Safety**: 
- Executes in sandboxed environment
- 15-second timeout
- Minimal PATH
- Logs failures to memory

#### AnalyzeTool
**Purpose**: Evaluate test results for success

**Inputs**:
- `skill_name`: Skill being analyzed
- `goal`: Original goal
- `test_result`: Output from test

**Outputs**:
- `success`: True if LLM determines skill works
- `analysis`: LLM's evaluation
- `message`: Human-readable result

**Uses LLM**: Invokes LLM to analyze output

#### MemoryTool
**Purpose**: Manage persistent memory

**Operations**:
- `add_skill`: Record a new skill
- `get_memory`: Retrieve full memory state
- `get_failures`: Get relevant past failures

**Outputs**:
- `success`: True if operation completed
- `data`: Retrieved data (for get operations)

**Persistence**: All changes written to memory.json

### Adding New Tools

To add a new tool:

1. **Create tool class**:
```python
class MyNewTool(AgentTool):
    def __init__(self, dependencies):
        super().__init__(
            name="my_tool",
            description="What the tool does - LLM sees this"
        )
        self.dependencies = dependencies
    
    def execute(self, **kwargs) -> dict:
        # Implement tool logic
        return {
            "success": True,
            "result": "..."
        }
```

2. **Register in AutonomousAgent.__init__**:
```python
self.tools = {
    # ... existing tools ...
    "my_tool": MyNewTool(dependencies),
}
```

3. **LLM automatically sees it** in available tools list

## Safety & Security

### Multi-Layer Security

#### Layer 1: Code Pattern Detection
Before any code is saved or executed:
- Scans for `eval()`, `exec()`, `os.system()`, etc.
- Blocks `__import__()`, `compile()`
- Prevents write operations outside workspace
- Uses regex patterns to catch dangerous code

#### Layer 2: Workspace Isolation
All file operations restricted to `./agent_workspace/`:
- Path traversal blocked (`..` rejected)
- Absolute paths blocked (`/etc/passwd` rejected)
- Verified at SafetyEnforcer initialization
- Enforced on every file operation

#### Layer 3: Execution Sandbox
Code execution happens in restricted environment:
- 15-second hard timeout
- Minimal PATH (`/usr/bin:/bin` only)
- Isolated PYTHONPATH
- Captures stdout/stderr
- Automatic cleanup of temporary files

#### Layer 4: Tiered Autonomy
Actions categorized by risk level:

**Auto-Approved** (no intervention needed):
- Write `.py` to `./agent_workspace/skills/`
- Execute Python from workspace
- Read/write within workspace

**Requires Approval** (future enhancement):
- File operations outside workspace
- Network access
- System commands

### Security Testing

All security features validated in test suite:
- ✅ Path traversal detection
- ✅ Absolute path blocking
- ✅ Dangerous pattern recognition
- ✅ Workspace isolation verification
- ✅ Execution timeout enforcement
- ✅ Safe code acceptance

## Memory & Learning

### Memory Structure

```json
{
  "version": 8,
  "created_at": "2026-02-07T10:00:00",
  "updated_at": "2026-02-07T12:30:00",
  
  "skills": [
    {
      "name": "factorial",
      "description": "Calculate factorial of number",
      "status": "working",
      "created_at": "2026-02-07T10:15:00",
      "updated_at": "2026-02-07T10:18:00"
    }
  ],
  
  "failures": [
    {
      "skill": "factorial",
      "error": "SyntaxError: invalid syntax",
      "code_snippet": "def factorial(n):\nreturn n * factorial(n-1",
      "timestamp": "2026-02-07T10:16:00"
    }
  ],
  
  "directives": [
    {
      "goal": "Create factorial function",
      "status": "completed",
      "created_at": "2026-02-07T10:15:00",
      "completed_at": "2026-02-07T10:18:00"
    }
  ]
}
```

### Learning from Failures

When a skill fails, the failure is:
1. Logged to memory with error and code snippet
2. Retrieved in future iterations as context
3. Passed to LLM in planning prompt
4. Used to avoid repeating mistakes

Example planning prompt with failure context:
```
GOAL: Create a factorial function
SKILL NAME: factorial
ITERATION: 3

PREVIOUS FAILURES TO AVOID:
- SyntaxError: invalid syntax
  Code: def factorial(n):\nreturn n * factorial(n-1...
- RecursionError: maximum recursion depth exceeded
  Code: def factorial(n):\nreturn n * factorial(n-1...

Based on these failures:
- Ensure proper base case (n <= 1)
- Include proper syntax (closing parentheses)
```

### Skill Lifecycle

```
┌─────────────┐
│   untested  │ ← Initial state
└──────┬──────┘
       │
       ├─ Test passes ──→ ┌─────────┐
       │                  │ working │
       │                  └─────────┘
       │
       └─ Max iterations ─→ ┌────────┐
                             │ failed │
                             └────────┘
```

## Performance Characteristics

### LLM-Central Mode
- **Iterations**: Variable (1-12, typically 3-5)
- **LLM Calls**: ~2-3 per iteration (decide + tool invocation)
- **Time**: 30-90 seconds per skill (depends on model)
- **Flexibility**: High - can adapt strategy mid-task
- **Autonomy**: True autonomous decision-making

### Graph Mode
- **Iterations**: Fixed workflow per iteration
- **LLM Calls**: 2 per iteration (plan + analyze)
- **Time**: 30-60 seconds per skill
- **Flexibility**: Low - same path every time
- **Autonomy**: Structured automation

## Extensibility

### Adding New Tools

The tool-based architecture makes extension easy:

1. **Create tool class** implementing AgentTool interface
2. **Register in agent** during initialization
3. **LLM discovers automatically** via description
4. **No prompt engineering needed** - LLM sees tool in context

Example extensions:
- **RefactorTool**: Improve existing code
- **DebugTool**: Add debugging statements
- **OptimizeTool**: Improve performance
- **DocumentTool**: Generate docstrings
- **SearchTool**: Search codebase for patterns

### Invoking LangGraph as a Tool

Future enhancement: Allow LLM to invoke LangGraph workflows

```python
class WorkflowTool(AgentTool):
    def __init__(self, graph):
        super().__init__(
            name="run_workflow",
            description="Execute structured workflow for complex multi-step tasks"
        )
        self.graph = graph
    
    def execute(self, workflow_type: str, **kwargs) -> dict:
        # Run LangGraph workflow
        result = self.graph.run(workflow_type, **kwargs)
        return {"success": True, "result": result}
```

Then LLM can decide:
```
DECISION: This task needs structured approach with multiple dependencies
ACTION: run_workflow
PARAMS: {"workflow_type": "multi_file_project", "goal": "..."}
```

## Migration Guide

### From Graph Mode to LLM-Central

**No code changes needed** - just switch mode:

```python
# Old: Graph mode (still supported)
agent = AutonomousAgent(mode="graph")

# New: LLM-central mode
agent = AutonomousAgent(mode="llm-central")
# Or just:
agent = AutonomousAgent()  # defaults to llm-central
```

### Command Line

```bash
# Use new mode (default)
python3 autonomous_agent.py

# Use legacy mode
python3 autonomous_agent.py --graph
```

### Configuration File

```python
# In autonomous_agent.py
AGENT_MODE = "llm-central"  # or "graph"
```

### Runtime Switching

```python
agent = AutonomousAgent(mode="llm-central")
# ... do some work ...
agent.mode = "graph"  # switch modes
# ... do more work ...
```

## Best Practices

### When to Use LLM-Central Mode

✅ **Use for**:
- Complex problem-solving tasks
- Exploratory development
- Tasks where optimal approach is unclear
- Research and experimentation
- Maximum autonomy desired

### When to Use Graph Mode

✅ **Use for**:
- Well-defined, repetitive tasks
- When you need predictable flow
- Debugging (easier to trace)
- Educational purposes (clear steps)
- Resource-constrained environments (fewer LLM calls)

### Optimizing LLM Decisions

Tips for better LLM decision-making:

1. **Clear Goals**: Provide specific, measurable goals
   - ✅ "Create a function that returns the factorial of n"
   - ❌ "Make a math thing"

2. **Context in Memory**: Let failures accumulate for learning
   - System automatically provides failure context
   - LLM learns from past mistakes

3. **Appropriate Model**: Choose model for task complexity
   - `qwen3-coder`: Complex code generation (32K context)
   - `glm-4.7-flash`: Simpler tasks (8K context, faster)

## Future Enhancements

### Planned Features

1. **Meta-Learning**: Agent improves its own decision-making
   - Track which action sequences work best
   - Learn optimal tool selection patterns
   - Adjust strategy based on success rates

2. **Multi-Agent Collaboration**: Multiple agents working together
   - One agent generates code, another reviews
   - Specialist agents for different languages
   - Coordinator agent for complex projects

3. **Tool Composition**: LLM chains multiple tools
   - Decides to invoke tools in sequence without iteration
   - "I'll plan, write, and test in one decision"

4. **LangGraph Integration**: LangGraph as invokable tool
   - LLM decides "this needs a workflow" → invokes graph
   - Best of both worlds: autonomy + structure

5. **External Tool Integration**:
   - Code formatters (black, prettier)
   - Linters (pylint, eslint)
   - Package managers (pip, npm)
   - Version control (git)

6. **Approval Workflows**: Human-in-the-loop for risky operations
   - LLM requests approval before system commands
   - User can review and approve/deny
   - Track approval patterns for future auto-approval

## Conclusion

The refactored architecture empowers the LLM as the true "brain" of the agent, making autonomous decisions about how to accomplish goals. LangGraph transitions from master orchestrator to optional coordination tool, available when the LLM decides it's needed.

This design:
- ✅ Maximizes agent autonomy
- ✅ Maintains all safety features
- ✅ Preserves backward compatibility
- ✅ Enables future extensibility
- ✅ Follows biological metaphor (brain/body/nervous system)

The agent can now truly reason about its actions rather than following a predetermined path, moving closer to genuine autonomous operation.
