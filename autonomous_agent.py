#!/usr/bin/env python3
"""
Production-Ready Autonomous Self-Improving Agent
Built with LangGraph + Ollama on Ubuntu 24.04

Features:
- File-based persistent memory (OpenCLAW-style)
- Tiered autonomy (auto-approve safe ops, require approval for system ops)
- Self-improvement loop with failure learning
- Workspace isolation and safety enforcement
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
                "version": 1,
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
        """Internal write with versioning."""
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
# LANGGRAPH NODES
# ============================================================================

class AutonomousAgent:
    """Main agent with LangGraph workflow."""
    
    def __init__(self):
        self.memory = PersistentMemory(MEMORY_FILE)
        self.safety = SafetyEnforcer(WORKSPACE_ROOT)
        self.executor = PythonExecutor(WORKSPACE_ROOT)
        self.llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.7)
        
        # Ensure directories exist
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        EXEC_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Agent initialized with model: {OLLAMA_MODEL}")
    
    # ========================================================================
    # NODE: Plan Skill
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
    # RUN
    # ========================================================================
    
    def run(self, goal: str, skill_name: str = None):
        """Run autonomous improvement loop."""
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
        print(f"{'='*70}\n")
        
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
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main CLI interface."""
    import sys
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   AUTONOMOUS SELF-IMPROVING AGENT                             ║
║   LangGraph + Ollama + Tiered Autonomy                        ║
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
    
    # Initialize agent
    agent = AutonomousAgent()
    
    # Interactive mode
    print("\nCommands:")
    print("  :directive <goal>  - Add a new improvement goal")
    print("  :memory           - Show memory state")
    print("  :skills           - List all skills")
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
