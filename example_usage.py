#!/usr/bin/env python3
"""
Example usage demonstrating the Autonomous Agent's capabilities.

Run this after setup to see the agent in action.
Demonstrates both LLM-central mode (default) and graph mode (legacy).
Includes new features: DIRECT_ANSWER, framework registry, and tool classification.
"""

from autonomous_agent import AutonomousAgent
import time


def demo_direct_answer():
    """Demo: DIRECT_ANSWER capability - LLM can respond without tools."""
    print("\n" + "="*70)
    print("DEMO: DIRECT_ANSWER Capability")
    print("="*70)
    print("""
This demo shows the agent's DIRECT_ANSWER capability where the LLM
can respond directly to simple questions without invoking tools.

Note: This demo is simulated as it requires actual LLM interaction.
The agent will decide when to use DIRECT_ANSWER vs tool-based flow.
    """)
    
    # Example scenarios where DIRECT_ANSWER would be used:
    scenarios = [
        ("What is Python?", "Simple factual question - can answer directly"),
        ("Explain list comprehensions", "Conceptual explanation - can answer directly"),
        ("Create a sorting algorithm", "Requires code generation - uses tools")
    ]
    
    for question, reasoning in scenarios:
        print(f"\nQuestion: {question}")
        print(f"Expected behavior: {reasoning}")
    
    print("\n✓ DIRECT_ANSWER allows the LLM to bypass tools for simple queries")
    time.sleep(1)


def demo_framework_registry():
    """Demo: Framework registry and tool assembly."""
    print("\n" + "="*70)
    print("DEMO: Framework Registry & Tool Assembly")
    print("="*70)
    
    from frameworks import FrameworkRegistry, register_default_frameworks
    
    registry = FrameworkRegistry()
    register_default_frameworks(registry)
    
    print(f"\nRegistered frameworks: {registry.list_frameworks()}")
    
    # Show framework types
    think_frameworks = registry.find_by_type("think")
    do_frameworks = registry.find_by_type("do")
    
    print(f"\nTHINK frameworks ({len(think_frameworks)}):")
    for fw in think_frameworks:
        print(f"  - {fw.name} ({fw.language})")
    
    print(f"\nDO frameworks ({len(do_frameworks)}):")
    for fw in do_frameworks:
        print(f"  - {fw.name} ({fw.language})")
    
    print("\n✓ Framework registry provides reusable code generation components")
    time.sleep(2)


def demo_tool_classification():
    """Demo: Tool classification (THINK vs DO)."""
    print("\n" + "="*70)
    print("DEMO: Tool Classification (THINK vs DO)")
    print("="*70)
    
    agent = AutonomousAgent()
    
    think_tools = agent.get_tools_by_type("think")
    do_tools = agent.get_tools_by_type("do")
    
    print(f"\nTHINK tools ({len(think_tools)}) - Planning & Analysis:")
    for name, tool in think_tools.items():
        print(f"  - {name}: {tool.description}")
    
    print(f"\nDO tools ({len(do_tools)}) - Execution & Action:")
    for name, tool in do_tools.items():
        print(f"  - {name}: {tool.description}")
    
    print("\n✓ Tool classification helps organize agent capabilities")
    time.sleep(2)


def demo_basic_skill(mode="llm-central"):
    """Demo 1: Create a simple skill."""
    print("\n" + "="*70)
    print(f"DEMO 1: Basic Skill Creation ({mode} mode)")
    print("="*70)
    
    agent = AutonomousAgent(mode=mode)
    agent.run(
        goal="Create a function that reverses a string",
        skill_name="string_reverser"
    )
    
    time.sleep(2)


def demo_data_processing(mode="llm-central"):
    """Demo 2: Data processing skill."""
    print("\n" + "="*70)
    print(f"DEMO 2: Data Processing Skill ({mode} mode)")
    print("="*70)
    
    agent = AutonomousAgent(mode=mode)
    agent.run(
        goal="Create a CSV parser that converts CSV text to a list of dictionaries",
        skill_name="csv_parser"
    )
    
    time.sleep(2)


def demo_validation(mode="llm-central"):
    """Demo 3: Validation skill."""
    print("\n" + "="*70)
    print(f"DEMO 3: Validation Skill ({mode} mode)")
    print("="*70)
    
    agent = AutonomousAgent(mode=mode)
    agent.run(
        goal="Create an email validator using regex",
        skill_name="email_validator"
    )
    
    time.sleep(2)


def demo_memory_inspection():
    """Demo 4: Inspect agent memory."""
    print("\n" + "="*70)
    print("DEMO 4: Memory Inspection")
    print("="*70)
    
    agent = AutonomousAgent()
    memory = agent.memory.read()
    
    print(f"\nTotal skills learned: {len(memory['skills'])}")
    print(f"Total failures logged: {len(memory['failures'])}")
    print(f"Memory version: {memory['version']}")
    
    print("\nSkills:")
    for skill in memory['skills']:
        status_emoji = {"working": "✅", "untested": "🔶", "failed": "❌"}
        emoji = status_emoji.get(skill['status'], "❓")
        print(f"  {emoji} {skill['name']}")
        print(f"     {skill['description']}")


def demo_batch_processing(mode="llm-central"):
    """Demo 5: Batch skill creation."""
    print("\n" + "="*70)
    print(f"DEMO 5: Batch Processing ({mode} mode)")
    print("="*70)
    
    goals = [
        ("Create a function to calculate factorial", "factorial"),
        ("Create a function to check if a number is prime", "prime_checker"),
        ("Create a function to generate Fibonacci sequence", "fibonacci")
    ]
    
    agent = AutonomousAgent(mode=mode)
    
    for goal, name in goals:
        print(f"\n→ Processing: {name}")
        agent.run(goal=goal, skill_name=name)
        time.sleep(1)
    
    # Show results
    memory = agent.memory.read()
    print(f"\n✅ Batch complete! Created {len(memory['skills'])} skills")


def demo_mode_comparison():
    """Demo 6: Compare LLM-central vs graph mode."""
    print("\n" + "="*70)
    print("DEMO 6: Mode Comparison")
    print("="*70)
    
    goal = "Create a function to check if a string is a palindrome"
    
    print("\n--- Testing LLM-CENTRAL MODE ---")
    agent_llm = AutonomousAgent(mode="llm-central")
    agent_llm.run(goal=goal, skill_name="palindrome_llm")
    
    time.sleep(2)
    
    print("\n--- Testing GRAPH MODE ---")
    agent_graph = AutonomousAgent(mode="graph")
    agent_graph.run(goal=goal, skill_name="palindrome_graph")
    
    print("\n✅ Both modes completed. Check agent_workspace/skills/ to compare results.")


def main():
    """Run all demos."""
    import sys
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║   AUTONOMOUS AGENT - EXAMPLE USAGE                            ║
╚═══════════════════════════════════════════════════════════════╝

This script demonstrates the agent's capabilities:
1. DIRECT_ANSWER capability (new)
2. Framework registry & tool assembly (new)
3. Tool classification: THINK vs DO (new)
4. Basic skill creation
5. Data processing
6. Validation logic
7. Memory inspection
8. Batch processing
9. Mode comparison (LLM-central vs Graph)

Each demo will run automatically. Press Ctrl+C to skip.
    """)
    
    input("Press Enter to start demos...")
    
    try:
        # New feature demos
        demo_direct_answer()
        demo_framework_registry()
        demo_tool_classification()
        
        # Original demos in LLM-central mode (default)
        demo_basic_skill(mode="llm-central")
        demo_data_processing(mode="llm-central")
        demo_validation(mode="llm-central")
        demo_memory_inspection()
        demo_batch_processing(mode="llm-central")
        
        # Mode comparison demo
        demo_mode_comparison()
        
        print("\n" + "="*70)
        print("✅ ALL DEMOS COMPLETE")
        print("="*70)
        print("\nNew features demonstrated:")
        print("  ✓ DIRECT_ANSWER - LLM can respond without tools")
        print("  ✓ Framework Registry - Reusable code components")
        print("  ✓ Tool Classification - THINK vs DO tools")
        print("  ✓ LangGraph Planner - Dynamic workflow execution")
        print("\nCheck agent_workspace/skills/ to see generated code!")
        print("Run 'python3 autonomous_agent.py' for interactive mode.")
        print("Use 'python3 autonomous_agent.py --graph' for legacy graph mode.")
        
    except KeyboardInterrupt:
        print("\n\nDemos interrupted. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
