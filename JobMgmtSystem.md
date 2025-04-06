# Job Management System for LocalGenius

## Overview
The Job Management System adds persistent tracking of tasks and their execution to LocalGenius. This enables resuming interrupted tasks, retrying failed steps, and maintaining a history of all work performed by the agent.

## New Components

### JobManager Class
The core component is the `JobManager` class which:
- Stores all job data in JSON files
- Tracks the status of jobs and individual steps
- Supports resuming interrupted jobs
- Enables retrying failed steps
- Maintains metadata and artifacts related to jobs

### AgentRunner Class
The `AgentRunner` class integrates the job management with the existing agent components:
- Handles CLI commands for task management
- Provides an interactive mode for task execution
- Integrates with the memory and planning systems
- Manages the execution lifecycle of tasks

## Job Structure

Each job contains:
- **ID**: Unique identifier (UUID)
- **Task**: The original task description
- **Status**: Current job status (pending, planning, running, etc.)
- **Plan**: List of planned steps
- **Steps**: Details of each execution step including status and results
- **Memory Context**: Similar tasks from memory used for planning
- **Artifacts**: Generated files and outputs from the job
- **Metadata**: Additional information about the job
- **Timestamps**: Creation and update times

## How to Use

### Interactive Mode
Run the agent in interactive mode:
```bash
python llama_dev_agent_v2.py
```

Commands:
- Enter a task description to execute a new task
- `list [limit]` - List recent jobs
- `show <job_id>` - Show details of a specific job
- `resume <job_id>` - Resume an interrupted job
- `abort <job_id>` - Abort a running job
- `retry <job_id> <step_index>` - Retry a specific step

### Command-Line Interface
The agent supports direct command-line operations:

```bash
# Create and run a new task
python llama_dev_agent_v2.py task "Create a Python script that scrapes Hacker News"

# List recent jobs
python llama_dev_agent_v2.py list --limit 5

# Show job details
python llama_dev_agent_v2.py show <job_id>

# Resume a job
python llama_dev_agent_v2.py resume <job_id>

# Retry a step
python llama_dev_agent_v2.py retry <job_id> <step_index>
```

## Next Steps

These enhancements make LocalGenius much more robust and enable longer, more complex development tasks by providing:

1. **Persistence**: Tasks survive program restarts
2. **Reliability**: Failed steps can be retried
3. **Visibility**: All work is tracked and viewable
4. **Flexibility**: Jobs can be paused, resumed, or aborted

In the next phase, we'll implement the Tools Registry system to expand the agent's capabilities.
