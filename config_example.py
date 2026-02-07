# Autonomous Agent Configuration
# Copy this to config.py and customize as needed

# Workspace Settings
WORKSPACE_DIR = "./agent_workspace"

# Ollama Settings
OLLAMA_MODEL = "qwen3-coder"  # Alternative: "glm-4.7-flash", "codellama", "deepseek-coder"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_TEMPERATURE = 0.7  # 0.0-1.0, higher = more creative

# Execution Settings
MAX_ITERATIONS = 12  # Maximum retry attempts per skill
EXECUTION_TIMEOUT = 15  # Seconds
AUTO_CLEANUP_EXEC = True  # Clean up exec/ directory

# Safety Settings
ENFORCE_WORKSPACE_ISOLATION = True
BLOCK_DANGEROUS_PATTERNS = True
REQUIRE_APPROVAL_FOR_SYSTEM_OPS = True

# Custom dangerous patterns (regex)
CUSTOM_DANGEROUS_PATTERNS = [
    # r"\brequests\.get\s*\(",  # Uncomment to block HTTP requests
    # r"\bsocket\.socket\s*\(",  # Uncomment to block socket operations
]

# Memory Settings
MEMORY_FILE = "memory.json"
MAX_FAILURE_HISTORY = 50  # Keep last N failures
AUTO_VERSION_INCREMENT = True

# Logging Settings
VERBOSE_MODE = True  # Print detailed progress
LOG_TO_FILE = False  # Save logs to agent.log
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Performance Settings
ENABLE_CACHING = True  # Cache LLM responses (experimental)
PARALLEL_EXECUTION = False  # Run multiple skills in parallel (experimental)

# Advanced Settings
SKILL_NAMING_STRATEGY = "auto"  # "auto", "sequential", "timestamp"
ALLOW_SKILL_UPDATES = True  # Allow updating existing skills
BACKUP_BEFORE_UPDATE = True  # Backup skills before modifying

# Model-specific Settings
MODEL_CONFIGS = {
    "qwen3-coder": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "context_window": 32768,
    },
    "glm-4.7-flash": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "context_window": 8192,
    },
    "codellama": {
        "temperature": 0.5,
        "max_tokens": 2048,
        "context_window": 16384,
    },
    "deepseek-coder": {
        "temperature": 0.6,
        "max_tokens": 4096,
        "context_window": 16384,
    }
}

# Feature Flags
FEATURES = {
    "self_improvement": True,
    "failure_learning": True,
    "human_directives": True,
    "batch_processing": True,
    "skill_versioning": False,  # Experimental
    "distributed_execution": False,  # Experimental
}

# UI Settings
SHOW_PROGRESS_BAR = False  # Requires tqdm
USE_COLORED_OUTPUT = True  # Requires colorama
EMOJI_INDICATORS = True

# Integration Settings
ENABLE_WEBHOOKS = False  # Send notifications
WEBHOOK_URL = ""  # Your webhook endpoint

# Export Settings
EXPORT_SKILLS_ON_SUCCESS = False  # Copy skills to exports/
EXPORT_DIRECTORY = "./exports"

# Development Settings
DEBUG_MODE = False
SAVE_INTERMEDIATE_STATES = False
ENABLE_PROFILING = False
