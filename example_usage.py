#!/usr/bin/env python3
"""
Example usage demonstrating the Autonomous Agent's capabilities.

Run this after setup to see the agent in action.
Demonstrates both LLM-central mode (default) and graph mode (legacy).
"""

from autonomous_agent import AutonomousAgent
import time


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
1. Basic skill creation
2. Data processing
3. Validation logic
4. Memory inspection
5. Batch processing
6. Mode comparison (LLM-central vs Graph)

Each demo will run automatically. Press Ctrl+C to skip.
    """)
    
    input("Press Enter to start demos...")
    
    try:
        # Run demos in LLM-central mode (default)
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
        print("\nCheck agent_workspace/skills/ to see generated code!")
        print("Run 'python3 autonomous_agent.py' for interactive mode.")
        print("Use 'python3 autonomous_agent.py --graph' for legacy graph mode.")
        
    except KeyboardInterrupt:
        print("\n\nDemos interrupted. Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
