#!/usr/bin/env python3
"""
Production-Ready Autonomous Self-Improving Agent
Built with Ollama + LangGraph on Ubuntu 24.04

ARCHITECTURE MODES:
- llm-central (default): LLM as brain/controller, LangGraph as coordination tool
- graph: LangGraph orchestrates fixed workflow (legacy mode)

Features:
- LLM-driven autonomous decision-making
- File-based persistent memory (OpenCLAW-style)
- Tiered autonomy (auto-approve safe ops, require approval for system ops)
- Self-improvement loop with failure learning
- Workspace isolation and safety enforcement
- Flexible tool-based architecture for extensibility
- Framework registry for composing reusable components
- Tool classification (THINK vs DO)
"""

import json
import operator
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from frameworks import Framework, FrameworkRegistry, ToolAssembler, register_default_frameworks


# ============================================================================
# CONFIGURATION
# ============================================================================

WORKSPACE_ROOT = Path("./agent_workspace").resolve()
MEMORY_FILE = WORKSPACE_ROOT / "memory.json"
SKILLS_DIR = WORKSPACE_ROOT / "skills"
EXEC_DIR = WORKSPACE_ROOT / "exec"

OLLAMA_MODEL = "qwen3-coder"  # Alternative: "glm-4.7-flash"
# See MODEL_GUIDE.md for detailed model comparison:
# - qwen3-coder: Best quality, 32K context, ~4.7GB, slower
# - glm-4.7-flash: Fastest, 8K context, ~2.6GB, good for simple tasks
MAX_ITERATIONS = 12
EXECUTION_TIMEOUT = 15

# Agent mode configuration
AGENT_MODE = "llm-central"  # Options: "llm-central" or "graph"
# - llm-central: LLM is the brain, decides all actions dynamically
# - graph: LangGraph orchestrates fixed workflow (legacy mode)

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bos\.system\s*\(",
    r"\bsubprocess\.Popen\s*\(",
    r"\bsubprocess\.call\s*\(",
    r"\b__import__\s*\(",
    r"\bcompile\s*\(",
    r"\bopen\s*\(.*([\'\"]w|[\'\"]a)",  # Write operations outside controlled context
]


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """LangGraph state with message accumulation."""
    messages: Annotated[list[BaseMessage], operator.add]
    current_goal: str
    iteration: int
    skill_name: str
    skill_code: str
    test_result: str
    status: str  # "planning", "coding", "testing", "analyzing", "success", "failed"
    requires_approval: bool
    pending_action: dict


# ============================================================================
# MEMORY SYSTEM (OpenCLAW-style)
# ============================================================================

class PersistentMemory:
    """File-based memory with versioning."""
    
    def __init__(self, memory_path: Path):
        self.memory_path = memory_path
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory structure
        if not self.memory_path.exists():
            self._write({
                "version": 0,  # Will become 1 after _write increments
                "skills": [],
                "failures": [],
                "directives": [],
                "created_at": datetime.now().isoformat()
            })
    
    def read(self) -> dict:
        """Read current memory state."""
        with open(self.memory_path, 'r') as f:
            return json.load(f)
    
    def _write(self, data: dict):
        """Internal write with versioning.
        
        Increments version on each write to track changes.
        Initial data with version=0 becomes version=1 on first write.
        """
        data["version"] = data.get("version", 0) + 1
        data["updated_at"] = datetime.now().isoformat()
        with open(self.memory_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_skill(self, name: str, description: str, status: str = "untested"):
        """Add or update skill in memory."""
        memory = self.read()
        
        # Check if skill exists
        for skill in memory["skills"]:
            if skill["name"] == name:
                skill["status"] = status
                skill["description"] = description
                skill["updated_at"] = datetime.now().isoformat()
                self._write(memory)
                return
        
        # Add new skill
        memory["skills"].append({
            "name": name,
            "description": description,
            "status": status,
            "created_at": datetime.now().isoformat()
        })
        self._write(memory)
    
    def log_failure(self, skill: str, error: str, code_snippet: str):
        """Log failure for learning."""
        memory = self.read()
        memory["failures"].append({
            "skill": skill,
            "error": error,
            "code_snippet": code_snippet,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 50 failures
        memory["failures"] = memory["failures"][-50:]
        self._write(memory)
    
    def add_directive(self, goal: str):
        """Add human directive."""
        memory = self.read()
        memory["directives"].append({
            "goal": goal,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        })
        self._write(memory)
        return len(memory["directives"]) - 1
    
    def complete_directive(self, index: int):
        """Mark directive as completed."""
        memory = self.read()
        if 0 <= index < len(memory["directives"]):
            memory["directives"][index]["status"] = "completed"
            memory["directives"][index]["completed_at"] = datetime.now().isoformat()
            self._write(memory)
    
    def get_relevant_failures(self, skill_name: str, limit: int = 5) -> list:
        """Get recent failures for context."""
        memory = self.read()
        relevant = [f for f in memory["failures"] if f["skill"] == skill_name]
        return relevant[-limit:]


# ============================================================================
# SAFETY SYSTEM
# ============================================================================

class SafetyEnforcer:
    """Enforces tiered autonomy and safety rules."""
    
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self._verify_workspace()
    
    def _verify_workspace(self):
        """Verify workspace is within current directory."""
        cwd = Path.cwd().resolve()
        assert str(self.workspace).startswith(str(cwd)), \
            f"Workspace {self.workspace} must be within {cwd}"
        print(f"✓ Workspace verified: {self.workspace}")
    
    def is_path_safe(self, path: str) -> tuple[bool, str]:
        """Check if path is within workspace."""
        try:
            target = (self.workspace / path).resolve()
            if not str(target).startswith(str(self.workspace)):
                return False, f"Path traversal detected: {path} escapes workspace"
            return True, ""
        except Exception as e:
            return False, f"Invalid path: {e}"
    
    def check_code_safety(self, code: str) -> tuple[bool, str]:
        """Check code for dangerous patterns."""
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"
        return True, ""
    
    def requires_approval(self, action: str, **kwargs) -> bool:
        """Determine if action requires human approval."""
        # AUTO-APPROVED actions
        auto_approved = [
            "write_skill",      # Write .py to workspace/skills/
            "execute_python",   # Run Python from workspace
            "read_workspace",   # Read from workspace
        ]
        
        if action in auto_approved:
            # Additional path check
            if "path" in kwargs:
                safe, _ = self.is_path_safe(kwargs["path"])
                return not safe
            return False
        
        # All other actions require approval
        return True


# ============================================================================
# EXECUTOR
# ============================================================================

class PythonExecutor:
    """Safe Python code executor."""
    
    def __init__(self, workspace: Path, timeout: int = EXECUTION_TIMEOUT):
        self.workspace = workspace
        self.exec_dir = workspace / "exec"
        self.exec_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
    
    def execute(self, code: str, skill_name: str) -> dict:
        """Execute Python code in sandboxed environment."""
        # Create temporary execution file
        exec_file = self.exec_dir / f"exec_{int(time.time() * 1000)}.py"
        
        try:
            exec_file.write_text(code)
            
            # Run with restricted environment
            result = subprocess.run(
                ["python3", str(exec_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.workspace),
                env={
                    "PYTHONPATH": str(self.workspace),
                    "PATH": "/usr/bin:/bin",  # Minimal PATH
                }
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timeout ({self.timeout}s)",
                "returncode": -1
            }
        
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
        
        finally:
            # Cleanup
            if exec_file.exists():
                exec_file.unlink()


# ============================================================================
# TOOL SYSTEM FOR LLM-CENTRAL MODE
# ============================================================================

class AgentTool:
    """Base class for agent tools that LLM can invoke."""
    
    def __init__(self, name: str, description: str, tool_type: str = None):
        self.name = name
        self.description = description
        self.tool_type = tool_type  # "think", "do", or None for legacy
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool and return result."""
        raise NotImplementedError


class PlanTool(AgentTool):
    """Tool for planning skill implementation."""
    
    def __init__(self, llm, memory, safety):
        super().__init__(
            name="plan_skill",
            description="Plan and generate Python code for a skill based on the goal. Returns generated code.",
            tool_type="think"
        )
        self.llm = llm
        self.memory = memory
        self.safety = safety
        self.assembler = None  # Will be injected by agent
    
    def execute(self, goal: str, skill_name: str, iteration: int = 1, frameworks: list = None) -> dict:
        """
        Generate skill code based on goal.
        
        Args:
            goal: Goal description
            skill_name: Name of the skill
            iteration: Current iteration number
            frameworks: Optional list of framework names to assemble
            
        Returns:
            Dictionary with success status, code, and message
        """
        # If frameworks are provided, use assembler
        if frameworks and self.assembler:
            params = {
                "description": goal,
                "function_name": skill_name,
                "params": "",
                "doc_string": goal,
                "test_params": "",
                "class_name": skill_name.title().replace("_", ""),
                "test_name": "basic",
                "test_description": goal,
            }
            
            result = self.assembler.assemble(frameworks, params)
            return result
        
        # Legacy: prompt-based plan generation (fallback)
        # Get relevant failures for context
        failures = self.memory.get_relevant_failures(skill_name)
        failure_context = ""
        if failures:
            failure_context = "\n\nPREVIOUS FAILURES TO AVOID:\n"
            for f in failures:
                failure_context += f"- {f['error']}\n  Code: {f['code_snippet'][:100]}...\n"
        
        prompt = f"""You are an autonomous Python skill developer. Create a complete, working Python skill.

GOAL: {goal}
SKILL NAME: {skill_name}
ITERATION: {iteration}/{MAX_ITERATIONS}

{failure_context}

REQUIREMENTS:
1. Write complete, self-contained Python code
2. Include proper error handling
3. Add a test harness at the bottom (if __name__ == "__main__":)
4. Make it production-ready and robust
5. Avoid patterns from previous failures

OUTPUT ONLY THE PYTHON CODE, nothing else. No markdown, no explanations."""

        messages = [SystemMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        # Extract code from response
        code = response.content.strip()
        
        # Remove markdown code blocks if present
        if code.startswith("```python"):
            code = code.split("```python", 1)[1]
            code = code.rsplit("```", 1)[0]
        elif code.startswith("```"):
            code = code.split("```", 1)[1]
            code = code.rsplit("```", 1)[0]
        
        code = code.strip()
        
        # Safety check
        safe, msg = self.safety.check_code_safety(code)
        if not safe:
            return {
                "success": False,
                "error": f"Safety check failed: {msg}",
                "code": ""
            }
        
        return {
            "success": True,
            "code": code,
            "message": f"Generated code ({len(code)} chars)"
        }


class WriteTool(AgentTool):
    """Tool for writing skill code to file."""
    
    def __init__(self):
        super().__init__(
            name="write_skill",
            description="Write skill code to a file in the skills directory. Returns success status.",
            tool_type="do"
        )
    
    def execute(self, skill_name: str, code: str) -> dict:
        """Write skill code to file."""
        skill_file = SKILLS_DIR / f"{skill_name}.py"
        
        try:
            skill_file.write_text(code)
            return {
                "success": True,
                "file_path": str(skill_file),
                "message": f"Skill written to {skill_file}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Write failed: {e}"
            }


class TestTool(AgentTool):
    """Tool for testing skill code."""
    
    def __init__(self, executor, memory):
        super().__init__(
            name="test_skill",
            description="Execute skill code and return test results. Returns success status and output.",
            tool_type="do"
        )
        self.executor = executor
        self.memory = memory
    
    def execute(self, skill_name: str, code: str) -> dict:
        """Execute skill and capture results."""
        result = self.executor.execute(code, skill_name)
        
        if result['success']:
            output = result['stdout']
            return {
                "success": True,
                "output": output,
                "message": "Test passed"
            }
        else:
            output = f"ERROR:\n{result['stderr']}\n\nOUTPUT:\n{result['stdout']}"
            
            # Log failure to memory
            self.memory.log_failure(
                skill=skill_name,
                error=result['stderr'],
                code_snippet=code[:500]
            )
            
            return {
                "success": False,
                "output": output,
                "error": result['stderr'],
                "message": "Test failed"
            }


class AnalyzeTool(AgentTool):
    """Tool for analyzing test results."""
    
    def __init__(self, llm):
        super().__init__(
            name="analyze_results",
            description="Analyze test results to determine if skill is working. Returns analysis and success status.",
            tool_type="think"
        )
        self.llm = llm
    
    def execute(self, skill_name: str, goal: str, test_result: str) -> dict:
        """Analyze test results."""
        prompt = f"""Analyze this test result and determine if the skill is working correctly.

SKILL: {skill_name}
GOAL: {goal}

TEST RESULT:
{test_result}

Is the skill working correctly? Respond with:
- "SUCCESS: <brief reason>" if working
- "FAILURE: <specific error to fix>" if not working

Be strict: only mark as SUCCESS if output shows clear success."""

        messages = [SystemMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        analysis = response.content.strip()
        is_success = analysis.upper().startswith("SUCCESS")
        
        return {
            "success": is_success,
            "analysis": analysis,
            "message": analysis
        }


class MemoryTool(AgentTool):
    """Tool for memory operations."""
    
    def __init__(self, memory):
        super().__init__(
            name="memory_ops",
            description="Perform memory operations: add_skill, get_memory, get_failures. Returns operation result.",
            tool_type="do"
        )
        self.memory = memory
    
    def execute(self, operation: str, **kwargs) -> dict:
        """Execute memory operation."""
        try:
            if operation == "add_skill":
                self.memory.add_skill(
                    name=kwargs['skill_name'],
                    description=kwargs['description'],
                    status=kwargs.get('status', 'untested')
                )
                return {"success": True, "message": f"Skill {kwargs['skill_name']} added to memory"}
            
            elif operation == "get_memory":
                data = self.memory.read()
                return {"success": True, "data": data}
            
            elif operation == "get_failures":
                failures = self.memory.get_relevant_failures(
                    kwargs['skill_name'],
                    limit=kwargs.get('limit', 5)
                )
                return {"success": True, "failures": failures}
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}


class LangGraphPlannerTool(AgentTool):
    """Tool for building and running dynamic StateGraph workflows."""
    
    def __init__(self, llm):
        super().__init__(
            name="langgraph_planner",
            description="Build and run a dynamic LangGraph StateGraph workflow. Accepts steps and goal, returns result summary.",
            tool_type="think"
        )
        self.llm = llm
    
    def execute(self, steps: list, goal: str) -> dict:
        """
        Build and run a dynamic StateGraph.
        
        Args:
            steps: List of step descriptors with 'name' and 'handler' (or 'tool_name')
            goal: Overall goal for the workflow
            
        Returns:
            Dictionary with success status and result summary
        """
        try:
            # Define a simple state for dynamic planning
            class PlanState(TypedDict):
                goal: str
                current_step: int
                results: list
                status: str
            
            # Create workflow
            workflow = StateGraph(PlanState)
            
            # Add nodes for each step
            for idx, step in enumerate(steps):
                step_name = step.get('name', f'step_{idx}')
                
                def make_node_fn(step_desc, step_idx):
                    """Factory to create node function with correct closure."""
                    def node_fn(state: PlanState) -> PlanState:
                        print(f"  Executing step {step_idx + 1}/{len(steps)}: {step_desc.get('name', 'unnamed')}")
                        
                        # Simple execution - just record the step
                        state['current_step'] = step_idx + 1
                        state['results'].append({
                            'step': step_desc.get('name', 'unnamed'),
                            'status': 'completed'
                        })
                        
                        # Update status
                        if step_idx + 1 >= len(steps):
                            state['status'] = 'completed'
                        
                        return state
                    
                    return node_fn
                
                workflow.add_node(step_name, make_node_fn(step, idx))
            
            # Add edges to connect steps sequentially
            if steps:
                workflow.add_edge(START, steps[0].get('name', 'step_0'))
                for idx in range(len(steps) - 1):
                    current_step = steps[idx].get('name', f'step_{idx}')
                    next_step = steps[idx + 1].get('name', f'step_{idx + 1}')
                    workflow.add_edge(current_step, next_step)
                
                # Connect last step to end
                last_step = steps[-1].get('name', f'step_{len(steps) - 1}')
                workflow.add_edge(last_step, END)
            
            # Compile and run
            app = workflow.compile()
            
            initial_state = {
                'goal': goal,
                'current_step': 0,
                'results': [],
                'status': 'running'
            }
            
            print(f"🔧 Running LangGraph dynamic planner with {len(steps)} steps...")
            final_state = app.invoke(initial_state)
            
            return {
                'success': True,
                'message': f'Dynamic workflow completed {len(steps)} steps',
                'results': final_state.get('results', []),
                'status': final_state.get('status', 'unknown')
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'LangGraph planner failed: {e}'
            }


class LLMController:
    """LLM-centric controller that decides actions dynamically."""
    
    def __init__(self, llm, tools: dict, memory, safety):
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.safety = safety
        self.context = []  # Conversation context
    
    def decide_next_action(self, goal: str, skill_name: str, iteration: int, history: list) -> dict:
        """Ask LLM to decide the next action based on context."""
        
        # Build context from history
        history_text = "\n".join([
            f"- {h['action']}: {h.get('result', {}).get('message', 'N/A')}"
            for h in history[-5:]  # Last 5 actions
        ])
        
        # Get memory context
        mem_data = self.memory.read()
        skill_status = "new"
        for skill in mem_data.get('skills', []):
            if skill['name'] == skill_name:
                skill_status = skill['status']
                break
        
        tools_desc = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])
        
        prompt = f"""You are the autonomous agent's brain. You control all decisions and actions.

CURRENT GOAL: {goal}
SKILL NAME: {skill_name}
ITERATION: {iteration}/{MAX_ITERATIONS}
SKILL STATUS: {skill_status}

AVAILABLE TOOLS:
{tools_desc}

RECENT ACTIONS:
{history_text if history else "No actions yet"}

INSTRUCTIONS:
1. Analyze the current situation
2. Decide what to do next to accomplish the goal
3. Choose ONE tool to invoke, or use a special action:
   - DIRECT_ANSWER: When you can answer directly without invoking tools
   - COMPLETE: When the goal is fully achieved
   - RETRY_PLAN: When you need to regenerate the plan
   - FAILED: When max iterations reached without success

Respond in this EXACT format:
DECISION: <your reasoning>
ACTION: <tool_name or DIRECT_ANSWER or COMPLETE or RETRY_PLAN or FAILED>
PARAMS: <JSON dict of parameters for the tool or action>

Example (using a tool):
DECISION: Need to generate code first
ACTION: plan_skill
PARAMS: {{"goal": "{goal}", "skill_name": "{skill_name}", "iteration": {iteration}}}

Example (direct answer):
DECISION: This is a simple question I can answer directly
ACTION: DIRECT_ANSWER
PARAMS: {{"response": "The answer to your question is..."}}

Example (completion):
DECISION: Test passed, skill is working
ACTION: COMPLETE
PARAMS: {{}}

Example (failure):
DECISION: Max iterations reached without success
ACTION: FAILED
PARAMS: {{}}
"""
        
        messages = [SystemMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        # Parse response
        content = response.content.strip()
        
        try:
            # Extract decision, action, and params
            decision_match = re.search(r'DECISION:\s*(.+?)(?=\nACTION:)', content, re.DOTALL)
            action_match = re.search(r'ACTION:\s*(\w+)', content)
            params_match = re.search(r'PARAMS:\s*(\{.+\})', content, re.DOTALL)
            
            decision = decision_match.group(1).strip() if decision_match else "No reasoning provided"
            action = action_match.group(1).strip() if action_match else "plan_skill"
            
            # Parse params
            if params_match:
                params_str = params_match.group(1).strip()
                # Clean up potential multiline JSON
                params_str = re.sub(r'\s+', ' ', params_str)
                params = json.loads(params_str)
            else:
                params = {}
            
            return {
                "decision": decision,
                "action": action,
                "params": params
            }
        
        except Exception as e:
            # Fallback: default action based on iteration
            error_msg = f"Failed to parse LLM decision: {e}"
            print(f"⚠️  {error_msg}")
            print(f"Response: {content[:200]}...")
            
            # Log parse failure to memory for debugging
            self.memory.log_failure(
                skill="llm_controller",
                error=error_msg,
                code_snippet=content[:500]
            )
            
            # Default to planning if no code exists yet
            return {
                "decision": f"Parse error, defaulting to plan (error: {e})",
                "action": "plan_skill",
                "params": {"goal": goal, "skill_name": skill_name, "iteration": iteration}
            }


# ============================================================================
# LANGGRAPH NODES (FOR GRAPH MODE)
# ============================================================================

class AutonomousAgent:
    """Main agent supporting both LLM-central and graph modes."""
    
    def __init__(self, mode: str = None):
        self.memory = PersistentMemory(MEMORY_FILE)
        self.safety = SafetyEnforcer(WORKSPACE_ROOT)
        self.executor = PythonExecutor(WORKSPACE_ROOT)
        self.llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.7)
        
        # Determine mode
        self.mode = mode or AGENT_MODE
        
        # Initialize framework registry and assembler
        self.framework_registry = FrameworkRegistry()
        register_default_frameworks(self.framework_registry)
        self.assembler = ToolAssembler(self.framework_registry, self.safety)
        
        # Initialize tools for LLM-central mode
        plan_tool = PlanTool(self.llm, self.memory, self.safety)
        plan_tool.assembler = self.assembler  # Inject assembler into PlanTool
        
        self.tools = {
            "plan_skill": plan_tool,
            "write_skill": WriteTool(),
            "test_skill": TestTool(self.executor, self.memory),
            "analyze_results": AnalyzeTool(self.llm),
            "memory_ops": MemoryTool(self.memory),
            "langgraph_planner": LangGraphPlannerTool(self.llm)
        }
        
        # Initialize LLM controller for LLM-central mode
        self.controller = LLMController(self.llm, self.tools, self.memory, self.safety)
        
        # Ensure directories exist
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        EXEC_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Agent initialized with model: {OLLAMA_MODEL}")
        print(f"✓ Mode: {self.mode}")
    
    def get_tools_by_type(self, tool_type: str) -> dict:
        """
        Get tools filtered by type.
        
        Args:
            tool_type: Type of tools to filter ("think", "do", or None for legacy)
            
        Returns:
            Dictionary of tools matching the specified type
        """
        return {
            name: tool 
            for name, tool in self.tools.items() 
            if tool.tool_type == tool_type
        }
    
    # ========================================================================
    # NODE: Plan Skill (FOR GRAPH MODE)
    # ========================================================================
    
    def plan_skill(self, state: AgentState) -> AgentState:
        """Plan the skill implementation based on goal."""
        print(f"\n🧠 PLANNING: {state['current_goal']}")
        
        # Get relevant failures for context
        failures = self.memory.get_relevant_failures(state['skill_name'])
        failure_context = ""
        if failures:
            failure_context = "\n\nPREVIOUS FAILURES TO AVOID:\n"
            for f in failures:
                failure_context += f"- {f['error']}\n  Code: {f['code_snippet'][:100]}...\n"
        
        prompt = f"""You are an autonomous Python skill developer. Create a complete, working Python skill.

GOAL: {state['current_goal']}
SKILL NAME: {state['skill_name']}
ITERATION: {state['iteration']}/{MAX_ITERATIONS}

{failure_context}

REQUIREMENTS:
1. Write complete, self-contained Python code
2. Include proper error handling
3. Add a test harness at the bottom (if __name__ == "__main__":)
4. Make it production-ready and robust
5. Avoid patterns from previous failures

OUTPUT ONLY THE PYTHON CODE, nothing else. No markdown, no explanations."""

        messages = [SystemMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        # Extract code from response
        code = response.content.strip()
        
        # Remove markdown code blocks if present
        if code.startswith("```python"):
            code = code.split("```python", 1)[1]
            code = code.rsplit("```", 1)[0]
        elif code.startswith("```"):
            code = code.split("```", 1)[1]
            code = code.rsplit("```", 1)[0]
        
        code = code.strip()
        
        # Safety check
        safe, msg = self.safety.check_code_safety(code)
        if not safe:
            print(f"⚠️  Safety violation: {msg}")
            return {
                **state,
                "skill_code": "",
                "status": "failed",
                "messages": [AIMessage(content=f"Safety check failed: {msg}")]
            }
        
        return {
            **state,
            "skill_code": code,
            "status": "coding",
            "messages": [AIMessage(content=f"Generated code ({len(code)} chars)")]
        }
    
    # ========================================================================
    # NODE: Write Skill
    # ========================================================================
    
    def write_skill(self, state: AgentState) -> AgentState:
        """Write skill code to file."""
        print(f"\n📝 WRITING: {state['skill_name']}.py")
        
        skill_file = SKILLS_DIR / f"{state['skill_name']}.py"
        
        try:
            skill_file.write_text(state['skill_code'])
            print(f"✓ Skill written: {skill_file}")
            
            return {
                **state,
                "status": "testing",
                "messages": [AIMessage(content=f"Skill written to {skill_file}")]
            }
        
        except Exception as e:
            print(f"❌ Write failed: {e}")
            return {
                **state,
                "status": "failed",
                "messages": [AIMessage(content=f"Write failed: {e}")]
            }
    
    # ========================================================================
    # NODE: Test Skill
    # ========================================================================
    
    def test_skill(self, state: AgentState) -> AgentState:
        """Execute skill and capture results."""
        print(f"\n🧪 TESTING: {state['skill_name']}")
        
        result = self.executor.execute(state['skill_code'], state['skill_name'])
        
        if result['success']:
            print(f"✓ Test passed")
            output = result['stdout']
        else:
            print(f"❌ Test failed: {result['stderr']}")
            output = f"ERROR:\n{result['stderr']}\n\nOUTPUT:\n{result['stdout']}"
            
            # Log failure to memory
            self.memory.log_failure(
                skill=state['skill_name'],
                error=result['stderr'],
                code_snippet=state['skill_code'][:500]
            )
        
        return {
            **state,
            "test_result": output,
            "status": "analyzing",
            "messages": [AIMessage(content=f"Test result: {output[:200]}...")]
        }
    
    # ========================================================================
    # NODE: Analyze Results
    # ========================================================================
    
    def analyze_results(self, state: AgentState) -> AgentState:
        """Analyze test results and determine next step."""
        print(f"\n🔍 ANALYZING: Results")
        
        prompt = f"""Analyze this test result and determine if the skill is working correctly.

SKILL: {state['skill_name']}
GOAL: {state['current_goal']}

TEST RESULT:
{state['test_result']}

Is the skill working correctly? Respond with:
- "SUCCESS: <brief reason>" if working
- "FAILURE: <specific error to fix>" if not working

Be strict: only mark as SUCCESS if output shows clear success."""

        messages = [SystemMessage(content=prompt)]
        response = self.llm.invoke(messages)
        
        analysis = response.content.strip()
        print(f"Analysis: {analysis}")
        
        is_success = analysis.upper().startswith("SUCCESS")
        
        if is_success:
            # Update memory
            self.memory.add_skill(
                name=state['skill_name'],
                description=state['current_goal'],
                status="working"
            )
            status = "success"
        else:
            status = "planning" if state['iteration'] < MAX_ITERATIONS else "failed"
            if status == "failed":
                self.memory.add_skill(
                    name=state['skill_name'],
                    description=state['current_goal'],
                    status="failed"
                )
        
        return {
            **state,
            "status": status,
            "iteration": state['iteration'] + 1,
            "messages": [AIMessage(content=analysis)]
        }
    
    # ========================================================================
    # ROUTER: Determine Next Node
    # ========================================================================
    
    def router(self, state: AgentState) -> Literal["plan_skill", "write_skill", "test_skill", "analyze_results", "__end__"]:
        """Route to next node based on status."""
        status = state['status']
        
        if status == "success":
            print(f"\n✅ SUCCESS: Skill {state['skill_name']} is working!")
            return END
        
        elif status == "failed":
            print(f"\n❌ FAILED: Max iterations reached for {state['skill_name']}")
            return END
        
        elif status == "planning":
            return "plan_skill"
        
        elif status == "coding":
            return "write_skill"
        
        elif status == "testing":
            return "test_skill"
        
        elif status == "analyzing":
            return "analyze_results"
        
        else:
            return END
    
    # ========================================================================
    # BUILD GRAPH
    # ========================================================================
    
    def build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan_skill", self.plan_skill)
        workflow.add_node("write_skill", self.write_skill)
        workflow.add_node("test_skill", self.test_skill)
        workflow.add_node("analyze_results", self.analyze_results)
        
        # Add edges
        workflow.add_edge(START, "plan_skill")
        workflow.add_conditional_edges(
            "plan_skill",
            self.router
        )
        workflow.add_conditional_edges(
            "write_skill",
            self.router
        )
        workflow.add_conditional_edges(
            "test_skill",
            self.router
        )
        workflow.add_conditional_edges(
            "analyze_results",
            self.router
        )
        
        return workflow.compile()
    
    # ========================================================================
    # LLM-CENTRAL MODE RUN
    # ========================================================================
    
    def run_llm_central(self, goal: str, skill_name: str):
        """Run agent in LLM-central mode where LLM makes all decisions."""
        print(f"\n🧠 LLM-CENTRAL MODE: LLM is the brain, deciding all actions")
        
        iteration = 1
        history = []
        skill_code = ""
        
        while iteration <= MAX_ITERATIONS:
            print(f"\n{'─'*70}")
            print(f"🔄 Iteration {iteration}/{MAX_ITERATIONS}")
            print(f"{'─'*70}")
            
            # LLM decides next action
            decision = self.controller.decide_next_action(goal, skill_name, iteration, history)
            
            print(f"\n💭 DECISION: {decision['decision']}")
            print(f"⚡ ACTION: {decision['action']}")
            
            action = decision['action']
            params = decision['params']
            
            # Handle DIRECT_ANSWER
            if action == "DIRECT_ANSWER":
                response_text = params.get("response", "No response provided")
                print(f"\n💬 DIRECT ANSWER: {response_text}")
                # Don't increment iteration for direct answers
                return True
            
            # Handle completion
            if action == "COMPLETE":
                print(f"\n✅ SUCCESS: Skill {skill_name} is working!")
                self.memory.add_skill(
                    name=skill_name,
                    description=goal,
                    status="working"
                )
                return True
            
            # Handle failure
            if action == "FAILED":
                print(f"\n❌ FAILED: Max iterations reached for {skill_name}")
                self.memory.add_skill(
                    name=skill_name,
                    description=goal,
                    status="failed"
                )
                return False
            
            # Execute tool
            if action in self.tools:
                tool = self.tools[action]
                print(f"🔧 Executing tool: {action}")
                
                try:
                    result = tool.execute(**params)
                    
                    # Display result
                    if result.get('success'):
                        print(f"✓ {result.get('message', 'Success')}")
                        
                        # Track code and test results
                        if action == "plan_skill":
                            skill_code = result.get('code', '')
                            print(f"  Generated {len(skill_code)} characters of code")
                        elif action == "test_skill":
                            output = result.get('output', '')
                            print(f"  Output: {output[:200]}{'...' if len(output) > 200 else ''}")
                        elif action == "analyze_results":
                            analysis = result.get('analysis', '')
                            print(f"  Analysis: {analysis}")
                    else:
                        print(f"✗ {result.get('message', 'Failed')}")
                        if 'error' in result:
                            print(f"  Error: {result['error']}")
                    
                    # Add to history
                    history.append({
                        "action": action,
                        "params": params,
                        "result": result
                    })
                
                except Exception as e:
                    print(f"❌ Tool execution error: {e}")
                    history.append({
                        "action": action,
                        "params": params,
                        "result": {"success": False, "error": str(e)}
                    })
            
            else:
                print(f"⚠️  Unknown action: {action}, retrying...")
            
            iteration += 1
        
        # Max iterations reached
        print(f"\n❌ FAILED: Max iterations ({MAX_ITERATIONS}) reached")
        self.memory.add_skill(
            name=skill_name,
            description=goal,
            status="failed"
        )
        return False
    
    # ========================================================================
    # RUN (DISPATCHES TO APPROPRIATE MODE)
    # ========================================================================
    
    def run(self, goal: str, skill_name: str = None):
        """Run autonomous improvement loop in selected mode."""
        if skill_name is None:
            # Generate skill name from goal
            skill_name = goal.lower().replace(" ", "_")[:30]
            skill_name = re.sub(r'[^a-z0-9_]', '', skill_name)
        
        print(f"\n{'='*70}")
        print(f"🚀 STARTING AUTONOMOUS AGENT")
        print(f"{'='*70}")
        print(f"Goal: {goal}")
        print(f"Skill: {skill_name}")
        print(f"Workspace: {WORKSPACE_ROOT}")
        print(f"Mode: {self.mode}")
        print(f"{'='*70}\n")
        
        # Dispatch to appropriate mode
        if self.mode == "llm-central":
            return self.run_llm_central(goal, skill_name)
        else:
            return self.run_graph_mode(goal, skill_name)
    
    def run_graph_mode(self, goal: str, skill_name: str):
        """Run agent in graph mode (legacy LangGraph orchestration)."""
        print(f"\n📊 GRAPH MODE: LangGraph orchestrates fixed workflow")
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=goal)],
            current_goal=goal,
            iteration=1,
            skill_name=skill_name,
            skill_code="",
            test_result="",
            status="planning",
            requires_approval=False,
            pending_action={}
        )
        
        # Build and run graph
        app = self.build_graph()
        
        try:
            for event in app.stream(initial_state):
                # Process events
                for node_name, node_state in event.items():
                    if node_name != "__end__":
                        pass  # Already printing in nodes
            
            return True
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI interface."""
    import sys
    
    # Parse command-line arguments for mode selection
    mode = AGENT_MODE  # Default from config
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--mode", "-m"]:
            if len(sys.argv) > 2:
                mode = sys.argv[2]
        elif sys.argv[1] == "--graph":
            mode = "graph"
        elif sys.argv[1] == "--llm-central":
            mode = "llm-central"
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║   AUTONOMOUS SELF-IMPROVING AGENT                             ║
║   LLM-Controlled + Ollama + Tiered Autonomy                   ║
║   Mode: {mode.upper():^53} ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Check Ollama
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if OLLAMA_MODEL not in result.stdout:
            print(f"⚠️  Warning: Model '{OLLAMA_MODEL}' not found in Ollama")
            print(f"   Run: ollama pull {OLLAMA_MODEL}")
            print(f"   Alternative: ollama pull glm-4.7-flash (faster, lighter)")
            print(f"   See MODEL_GUIDE.md for comparison")
            sys.exit(1)
        print(f"✓ Ollama model '{OLLAMA_MODEL}' available")
        print(f"  See MODEL_GUIDE.md to compare qwen3-coder vs glm-4.7-flash\n")
    except Exception as e:
        print(f"❌ Ollama check failed: {e}")
        print("   Ensure Ollama is running: sudo systemctl start ollama")
        sys.exit(1)
    
    # Initialize agent with selected mode
    agent = AutonomousAgent(mode=mode)
    
    # Interactive mode
    print("\nCommands:")
    print("  :directive <goal>  - Add a new improvement goal")
    print("  :memory           - Show memory state")
    print("  :skills           - List all skills")
    print("  :mode <mode>      - Switch mode (llm-central or graph)")
    print("  :quit             - Exit")
    print()
    
    while True:
        try:
            user_input = input("Agent> ").strip()
            
            if not user_input:
                continue
            
            if user_input == ":quit":
                print("Goodbye!")
                break
            
            elif user_input == ":memory":
                memory = agent.memory.read()
                print(json.dumps(memory, indent=2))
            
            elif user_input == ":skills":
                memory = agent.memory.read()
                print(f"\nSkills ({len(memory['skills'])}):")
                for skill in memory['skills']:
                    status_emoji = {"working": "✅", "untested": "🔶", "failed": "❌"}
                    emoji = status_emoji.get(skill['status'], "❓")
                    print(f"  {emoji} {skill['name']}: {skill['description']}")
            
            elif user_input.startswith(":mode "):
                new_mode = user_input[6:].strip()
                if new_mode in ["llm-central", "graph"]:
                    agent.mode = new_mode
                    print(f"✓ Switched to {new_mode} mode")
                else:
                    print("Invalid mode. Options: llm-central, graph")
            
            elif user_input.startswith(":directive "):
                goal = user_input[11:].strip()
                if goal:
                    agent.run(goal)
                else:
                    print("Usage: :directive <goal>")
            
            else:
                # Direct goal
                agent.run(user_input)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type :quit to exit.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
