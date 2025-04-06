#!/usr/bin/env python3
# llama_dev_agent_v2.py - Enhanced version with job management

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_runner import AgentRunner

def main():
    """Main entry point for the LLaMA Dev Agent."""
    agent = AgentRunner()
    agent.run_cli()

if __name__ == "__main__":
    main()
