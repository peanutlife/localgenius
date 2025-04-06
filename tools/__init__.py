# tools/__init__.py

from .registry import ToolRegistry
from .exec import run_code
from .file_ops import read_file, write_file
from .git_tools import register_git_tools
from .web_tools import register_web_tools
from .db_tools import register_db_tools
import subprocess
import os
import json

# Create a global tool registry instance
registry = ToolRegistry()

# Register core tools
registry.register(
    "run_code",
    run_code,
    "Execute Python code and return the output"
)

registry.register(
    "read_file",
    read_file,
    "Read content from a file at the specified path"
)

registry.register(
    "write_file",
    write_file,
    "Write content to a file at the specified path"
)

# Add shell command execution tool
def run_shell(command, timeout=30):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command execution timed out"}
    except Exception as e:
        return {"error": str(e)}

registry.register(
    "run_shell",
    run_shell,
    "Execute a shell command and return stdout, stderr, and return code"
)

# Add file listing tool
def list_files(path="."):
    """List all files in a directory"""
    try:
        files = os.listdir(path)
        return files
    except Exception as e:
        return {"error": str(e)}

registry.register(
    "list_files",
    list_files,
    "List all files in a specified directory (defaults to current directory)"
)

# Add file existence check
def file_exists(path):
    """Check if a file exists"""
    return os.path.exists(path)

registry.register(
    "file_exists",
    file_exists,
    "Check if a file exists at the specified path"
)

# Add JSON tools
def read_json(path):
    """Read a JSON file and parse it"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

registry.register(
    "read_json",
    read_json,
    "Read and parse a JSON file at the specified path"
)

def write_json(path, data):
    """Write data to a JSON file"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

registry.register(
    "write_json",
    write_json,
    "Write data to a JSON file at the specified path"
)

# Register Git tools
register_git_tools(registry)

# Register Web tools
register_web_tools(registry)

# Register Database tools
register_db_tools(registry)

# Function to get all registered tools
def get_registry():
    """Get the tool registry"""
    return registry
