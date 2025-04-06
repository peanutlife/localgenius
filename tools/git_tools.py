# tools/git_tools.py

import subprocess
import os
from .registry import ToolRegistry

def git_status():
    """Get the current Git repository status"""
    try:
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def git_diff(file_path=None):
    """Get the diff of changes in the repository or for a specific file"""
    try:
        cmd = ["git", "diff"]
        if file_path:
            cmd.append(file_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def git_add(file_path="."):
    """Add files to Git staging area"""
    try:
        result = subprocess.run(
            ["git", "add", file_path],
            capture_output=True,
            text=True
        )
        return f"Added {file_path} to staging area" if not result.stderr else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

def git_commit(message):
    """Commit staged changes to Git repository"""
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def git_log(n=5):
    """Get the Git commit history"""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def git_clone(repo_url, target_dir=None):
    """Clone a Git repository"""
    try:
        cmd = ["git", "clone", repo_url]
        if target_dir:
            cmd.append(target_dir)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        return result.stdout if not result.stderr else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

def git_checkout(branch):
    """Checkout a Git branch"""
    try:
        result = subprocess.run(
            ["git", "checkout", branch],
            capture_output=True,
            text=True
        )
        return result.stdout if not result.stderr else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

def git_branch():
    """List Git branches"""
    try:
        result = subprocess.run(
            ["git", "branch"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

def register_git_tools(registry):
    """Register all Git tools with the given registry"""
    registry.register(
        "git_status",
        git_status,
        "Get the current Git repository status"
    )

    registry.register(
        "git_diff",
        git_diff,
        "Get the diff of changes in the repository or for a specific file"
    )

    registry.register(
        "git_add",
        git_add,
        "Add files to Git staging area (defaults to all files)"
    )

    registry.register(
        "git_commit",
        git_commit,
        "Commit staged changes to Git repository with the specified message"
    )

    registry.register(
        "git_log",
        git_log,
        "Get the Git commit history (defaults to last 5 commits)"
    )

    registry.register(
        "git_clone",
        git_clone,
        "Clone a Git repository to the specified directory"
    )

    registry.register(
        "git_checkout",
        git_checkout,
        "Checkout a Git branch"
    )

    registry.register(
        "git_branch",
        git_branch,
        "List Git branches"
    )

    return registry
