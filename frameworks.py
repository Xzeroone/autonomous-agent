#!/usr/bin/env python3
"""
Framework Registry and Tool Assembly System

Provides a registry of reusable code generation frameworks and components,
and an assembler that can compose frameworks into deliverables.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
import re


@dataclass
class Framework:
    """Represents a reusable framework or component for code generation."""
    
    name: str
    type_: Literal["think", "do"]
    language: str
    components: Dict[str, str] = field(default_factory=dict)
    
    def render(self, params: Dict[str, str]) -> str:
        """
        Render the framework with provided parameters.
        
        Args:
            params: Dictionary of parameters to substitute in templates
            
        Returns:
            Rendered framework text with parameters substituted
        """
        result = []
        
        for component_name, template in self.components.items():
            # Substitute parameters in template
            rendered = template
            for key, value in params.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            result.append(f"# Component: {component_name}")
            result.append(rendered)
            result.append("")
        
        return "\n".join(result)


class FrameworkRegistry:
    """Registry for managing and retrieving frameworks."""
    
    def __init__(self):
        self._frameworks: Dict[str, Framework] = {}
    
    def register(self, framework: Framework) -> None:
        """
        Register a framework in the registry.
        
        Args:
            framework: Framework to register
        """
        self._frameworks[framework.name] = framework
    
    def get(self, name: str) -> Optional[Framework]:
        """
        Retrieve a framework by name.
        
        Args:
            name: Name of the framework
            
        Returns:
            Framework if found, None otherwise
        """
        return self._frameworks.get(name)
    
    def list_frameworks(self) -> List[str]:
        """
        List all registered framework names.
        
        Returns:
            List of framework names
        """
        return list(self._frameworks.keys())
    
    def find_by_type(self, type_: Literal["think", "do"]) -> List[Framework]:
        """
        Find all frameworks of a specific type.
        
        Args:
            type_: Framework type ("think" or "do")
            
        Returns:
            List of frameworks matching the type
        """
        return [fw for fw in self._frameworks.values() if fw.type_ == type_]
    
    def find_by_language(self, language: str) -> List[Framework]:
        """
        Find all frameworks for a specific language.
        
        Args:
            language: Programming language
            
        Returns:
            List of frameworks for the language
        """
        return [fw for fw in self._frameworks.values() if fw.language.lower() == language.lower()]


class ToolAssembler:
    """Assembles frameworks into deliverables with safety checks."""
    
    def __init__(self, registry: FrameworkRegistry, safety_enforcer=None):
        """
        Initialize the tool assembler.
        
        Args:
            registry: FrameworkRegistry instance
            safety_enforcer: Optional SafetyEnforcer for code validation
        """
        self.registry = registry
        self.safety_enforcer = safety_enforcer
    
    def assemble(self, framework_names: List[str], params: Dict[str, str]) -> dict:
        """
        Assemble frameworks into a deliverable.
        
        Args:
            framework_names: List of framework names to assemble
            params: Parameters for rendering frameworks
            
        Returns:
            Dictionary with success status, assembled code/source, and message
        """
        if not framework_names:
            return {
                "success": False,
                "error": "No frameworks specified",
                "code": "",
                "message": "Assembly failed: no frameworks specified"
            }
        
        # Collect rendered components
        rendered_parts = []
        
        for fw_name in framework_names:
            framework = self.registry.get(fw_name)
            if not framework:
                return {
                    "success": False,
                    "error": f"Framework not found: {fw_name}",
                    "code": "",
                    "message": f"Assembly failed: framework '{fw_name}' not found"
                }
            
            rendered = framework.render(params)
            rendered_parts.append(f"# Framework: {fw_name} (type: {framework.type_}, language: {framework.language})")
            rendered_parts.append(rendered)
        
        # Concatenate all parts
        assembled_code = "\n".join(rendered_parts)
        
        # Safety check if enforcer is available
        if self.safety_enforcer:
            safe, msg = self.safety_enforcer.check_code_safety(assembled_code)
            if not safe:
                return {
                    "success": False,
                    "error": f"Safety check failed: {msg}",
                    "code": assembled_code,
                    "message": f"Assembly failed: safety violation - {msg}"
                }
        
        return {
            "success": True,
            "code": assembled_code,
            "source": assembled_code,  # Alias for compatibility
            "message": f"Successfully assembled {len(framework_names)} framework(s)"
        }


def register_default_frameworks(registry: FrameworkRegistry) -> None:
    """
    Register minimal example frameworks.
    
    Args:
        registry: FrameworkRegistry to populate with defaults
    """
    # Python generator framework
    python_generator = Framework(
        name="python_generator",
        type_="do",
        language="python",
        components={
            "header": """#!/usr/bin/env python3
\"\"\"
{description}
\"\"\"
""",
            "main_function": """
def {function_name}({params}):
    \"\"\"
    {doc_string}
    \"\"\"
    # TODO: Implement function logic
    pass
""",
            "test_harness": """
if __name__ == "__main__":
    # Test harness
    print("Testing {function_name}...")
    result = {function_name}({test_params})
    print(f"Result: {{result}}")
"""
        }
    )
    
    # Analysis prompt framework
    analysis_prompt = Framework(
        name="analysis_prompt",
        type_="think",
        language="natural",
        components={
            "analysis_template": """
ANALYSIS TASK: {task}

CONTEXT:
{context}

APPROACH:
1. {step1}
2. {step2}
3. {step3}

EXPECTED OUTCOME:
{expected_outcome}
"""
        }
    )
    
    # Test harness framework
    test_harness = Framework(
        name="test_harness",
        type_="do",
        language="python",
        components={
            "test_setup": """
import unittest

class Test{class_name}(unittest.TestCase):
    \"\"\"Test suite for {class_name}.\"\"\"
    
    def setUp(self):
        \"\"\"Set up test fixtures.\"\"\"
        pass
""",
            "test_method": """
    def test_{test_name}(self):
        \"\"\"Test {test_description}.\"\"\"
        # TODO: Implement test
        self.assertTrue(True)
""",
            "test_runner": """
if __name__ == '__main__':
    unittest.main()
"""
        }
    )
    
    # Register all default frameworks
    registry.register(python_generator)
    registry.register(analysis_prompt)
    registry.register(test_harness)
