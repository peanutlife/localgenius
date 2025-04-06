# agent_runner.py

import os
import sys
import argparse
from models.llama3_runner import LlamaRunner
from memory import Memory
from tasks import TaskPlanner
from jobs.job_manager import JobManager, JobStatus, StepStatus
import time
from typing import Optional

class AgentRunner:
    def __init__(self):
        """Initialize the agent runner with all required components."""
        # Create necessary directories
        os.makedirs("workspace", exist_ok=True)

        # Initialize components
        self.llm = LlamaRunner(model_name="llama3:8b")
        self.memory = Memory()
        self.planner = TaskPlanner(self.llm)
        self.job_manager = JobManager()

    def run_cli(self):
        """Run the agent in CLI mode."""
        parser = argparse.ArgumentParser(description="LocalGenius - Local AI Development Agent")
        subparsers = parser.add_subparsers(dest="command", help="Command to run")

        # New task command
        task_parser = subparsers.add_parser("task", help="Create and run a new task")
        task_parser.add_argument("description", nargs="?", help="Task description")

        # List jobs command
        list_parser = subparsers.add_parser("list", help="List all jobs")
        list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of jobs to show")
        list_parser.add_argument("--status", help="Filter by status (pending, running, completed, etc.)")

        # Resume job command
        resume_parser = subparsers.add_parser("resume", help="Resume a paused or incomplete job")
        resume_parser.add_argument("job_id", help="ID of the job to resume")

        # Show job details command
        show_parser = subparsers.add_parser("show", help="Show details of a specific job")
        show_parser.add_argument("job_id", help="ID of the job to show")

        # Abort job command
        abort_parser = subparsers.add_parser("abort", help="Abort a running job")
        abort_parser.add_argument("job_id", help="ID of the job to abort")

        # Retry step command
        retry_parser = subparsers.add_parser("retry", help="Retry a specific step in a job")
        retry_parser.add_argument("job_id", help="ID of the job")
        retry_parser.add_argument("step_index", type=int, help="Index of the step to retry")

        # Parse arguments
        args = parser.parse_args()

        # If no command is provided, enter interactive mode
        if not args.command:
            self.interactive_mode()
            return

        # Handle commands
        if args.command == "task":
            if not args.description:
                description = input("Enter task description: ")
            else:
                description = args.description
            job_id = self.execute_task(description)
            print(f"Job completed with ID: {job_id}")

        elif args.command == "list":
            jobs = self.job_manager.list_jobs(args.limit, args.status)
            self._print_job_list(jobs)

        elif args.command == "resume":
            success = self.resume_job(args.job_id)
            if success:
                print(f"Successfully resumed job {args.job_id}")
            else:
                print(f"Failed to resume job {args.job_id}")

        elif args.command == "show":
            job = self.job_manager.get_job(args.job_id)
            if job:
                self._print_job_details(job)
            else:
                print(f"Job {args.job_id} not found")

        elif args.command == "abort":
            success = self.job_manager.abort_job(args.job_id)
            if success:
                print(f"Successfully aborted job {args.job_id}")
            else:
                print(f"Failed to abort job {args.job_id}")

        elif args.command == "retry":
            success = self.retry_step(args.job_id, args.step_index)
            if success:
                print(f"Successfully retried step {args.step_index} of job {args.job_id}")
            else:
                print(f"Failed to retry step {args.step_index} of job {args.job_id}")

    def interactive_mode(self):
        """Run the agent in interactive CLI mode."""
        print("\n🧠 LLaMA Dev Agent Ready. Type a task (e.g., 'create a Flask app'). Type 'exit' to quit.\n")

        while True:
            user_input = input(">> ").strip()

            if user_input.lower() in ["exit", "quit"]:
                break

            # Handle special commands
            if user_input.startswith("list"):
                limit = 10
                if len(user_input.split()) > 1:
                    try:
                        limit = int(user_input.split()[1])
                    except ValueError:
                        pass
                jobs = self.job_manager.list_jobs(limit)
                self._print_job_list(jobs)
                continue

            if user_input.startswith("show "):
                job_id = user_input.split("show ")[1].strip()
                job = self.job_manager.get_job(job_id)
                if job:
                    self._print_job_details(job)
                else:
                    print(f"Job {job_id} not found")
                continue

            if user_input.startswith("resume "):
                job_id = user_input.split("resume ")[1].strip()
                success = self.resume_job(job_id)
                if success:
                    print(f"Successfully resumed job {job_id}")
                else:
                    print(f"Failed to resume job {job_id}")
                continue

            if user_input.startswith("abort "):
                job_id = user_input.split("abort ")[1].strip()
                success = self.job_manager.abort_job(job_id)
                if success:
                    print(f"Successfully aborted job {job_id}")
                else:
                    print(f"Failed to abort job {job_id}")
                continue

            if user_input.startswith("retry "):
                parts = user_input.split("retry ")[1].strip().split()
                if len(parts) == 2:
                    job_id, step_index = parts
                    try:
                        step_index = int(step_index)
                        success = self.retry_step(job_id, step_index)
                        if success:
                            print(f"Successfully retried step {step_index} of job {job_id}")
                        else:
                            print(f"Failed to retry step {step_index} of job {job_id}")
                    except ValueError:
                        print("Invalid step index. Please provide a number.")
                else:
                    print("Invalid command. Format: retry <job_id> <step_index>")
                continue

            # Execute a new task
            job_id = self.execute_task(user_input)
            print(f"\n✅ Task completed. Job ID: {job_id}")

    def execute_task(self, task_description: str) -> str:
        """
        Execute a new task with the given description.

        Args:
            task_description: Description of the task to execute

        Returns:
            ID of the created job
        """
        # Log task to memory
        self.memory.log_task(task_description)

        # Create a new job
        job_id = self.job_manager.create_job(task_description)
        print(f"Created job with ID: {job_id}")

        # Update job status to planning
        self.job_manager.update_job_status(job_id, JobStatus.PLANNING)

        # Search for similar tasks in memory
        similar = self.memory.search_memory(task_description)
        if similar:
            print("🔍 Found similar tasks in memory:")
            for i, match in enumerate(similar, 1):
                print(f"{i}. {match[:200]}{'...' if len(match) > 200 else ''}")
            print()

            # Save memory context to job
            self.job_manager.set_memory_context(job_id, similar)

        # Generate plan
        print("\n🛠️  Planning task...\n")
        plan = self.planner.plan_task(task_description, memory_context=similar)

        # Log plan to memory
        self.memory.log_plan(plan)

        # Save plan to job
        self.job_manager.set_job_plan(job_id, plan)

        # Execute each step
        for step_index, step in enumerate(plan):
            # Skip if job is aborted or paused
            job = self.job_manager.get_job(job_id)
            if job['status'] in [JobStatus.ABORTED.value, JobStatus.PAUSED.value]:
                print(f"Job {job_id} is {job['status']}. Stopping execution.")
                break

            print(f"➡️ Step {step_index + 1}: {step}")

            # Mark step as running
            self.job_manager.start_step(job_id, step_index)

            try:
                # Execute the step
                result = self.planner.execute_step(step)

                # Log result to memory
                self.memory.log_result(step, result)

                # Mark step as completed
                self.job_manager.complete_step(job_id, step_index, result)

                print(f"✅ Result: {result}\n")
            except Exception as e:
                error_message = f"Error executing step: {str(e)}"
                print(f"❌ {error_message}")

                # Mark step as failed
                self.job_manager.complete_step(job_id, step_index, error_message, StepStatus.FAILED)

        # Final job status is set automatically by the job manager based on steps
        return job_id

    def resume_job(self, job_id: str) -> bool:
        """
        Resume execution of a paused or incomplete job.

        Args:
            job_id: ID of the job to resume

        Returns:
            True if successful, False otherwise
        """
        job = self.job_manager.get_job(job_id)
        if not job:
            print(f"Job {job_id} not found")
            return False

        # Can only resume paused or running jobs
        if job['status'] not in [JobStatus.PAUSED.value, JobStatus.RUNNING.value]:
            print(f"Cannot resume job with status {job['status']}")
            return False

        # Set job status to running
        self.job_manager.update_job_status(job_id, JobStatus.RUNNING)

        # Find the first incomplete step
        for step_index, step in enumerate(job['steps']):
            if step['status'] in [StepStatus.PENDING.value, StepStatus.RUNNING.value]:
                print(f"Resuming from step {step_index + 1}: {step['description']}")

                # Execute this step and all remaining steps
                for i in range(step_index, len(job['steps'])):
                    current_step = job['steps'][i]

                    # Skip if job is aborted or paused
                    current_job = self.job_manager.get_job(job_id)
                    if current_job['status'] in [JobStatus.ABORTED.value, JobStatus.PAUSED.value]:
                        print(f"Job {job_id} is {current_job['status']}. Stopping execution.")
                        break

                    print(f"➡️ Step {i + 1}: {current_step['description']}")

                    # Mark step as running
                    self.job_manager.start_step(job_id, i)

                    try:
                        # Execute the step
                        result = self.planner.execute_step(current_step['description'])

                        # Log result to memory
                        self.memory.log_result(current_step['description'], result)

                        # Mark step as completed
                        self.job_manager.complete_step(job_id, i, result)

                        print(f"✅ Result: {result}\n")
                    except Exception as e:
                        error_message = f"Error executing step: {str(e)}"
                        print(f"❌ {error_message}")

                        # Mark step as failed
                        self.job_manager.complete_step(job_id, i, error_message, StepStatus.FAILED)

                return True

        print("No incomplete steps found. Job is already complete.")
        return False

    def retry_step(self, job_id: str, step_index: int) -> bool:
        """
        Retry a specific step in a job.

        Args:
            job_id: ID of the job
            step_index: Index of the step to retry

        Returns:
            True if successful, False otherwise
        """
        job = self.job_manager.get_job(job_id)
        if not job:
            print(f"Job {job_id} not found")
            return False

        # Validate step index
        if step_index < 0 or step_index >= len(job['steps']):
            print(f"Invalid step index {step_index}. Job has {len(job['steps'])} steps.")
            return False

        # Get the step to retry
        step = job['steps'][step_index]
        print(f"🔁 Retrying step {step_index + 1}: {step['description']}")

        # Mark step as running
        self.job_manager.start_step(job_id, step_index)

        try:
            # Execute the step
            result = self.planner.execute_step(step['description'])

            # Log result to memory
            self.memory.log_result(step['description'], result)

            # Mark step as completed
            self.job_manager.complete_step(job_id, step_index, result)

            print(f"✅ Result: {result}\n")
            return True
        except Exception as e:
            error_message = f"Error executing step: {str(e)}"
            print(f"❌ {error_message}")

            # Mark step as failed
            self.job_manager.complete_step(job_id, step_index, error_message, StepStatus.FAILED)
            return False

    def _print_job_list(self, jobs):
        """Print a formatted list of jobs."""
        if not jobs:
            print("No jobs found.")
            return

        print(f"\n{'ID':<36} {'Status':<10} {'Task':<50} {'Created':<20}")
        print("-" * 110)

        for job in jobs:
            # Truncate task description if too long
            task = job['task']
            if len(task) > 47:
                task = task[:47] + "..."

            # Format date to be more readable
            created_at = job.get('created_at', '')
            if created_at:
                try:
                    dt = created_at.split('T')[0]
                    time = created_at.split('T')[1].split('.')[0]
                    created_at = f"{dt} {time}"
                except:
                    pass

            print(f"{job['id']:<36} {job['status']:<10} {task:<50} {created_at:<20}")
        print()

    def _print_job_details(self, job):
        """Print detailed information about a job."""
        print("\n" + "=" * 80)
        print(f"Job ID: {job['id']}")
        print(f"Status: {job['status']}")
        print(f"Task: {job['task']}")
        print(f"Created: {job['created_at']}")
        print(f"Updated: {job['updated_at']}")
        print("=" * 80)

        # Print plan
        print("\nPlan:")
        for i, step_desc in enumerate(job['plan']):
            print(f"{i+1}. {step_desc}")

        # Print steps with results
        print("\nExecution Steps:")
        for i, step in enumerate(job['steps']):
            status_icon = "✅" if step['status'] == StepStatus.COMPLETED.value else "❌" if step['status'] == StepStatus.FAILED.value else "⏳" if step['status'] == StepStatus.RUNNING.value else "⏸️"
            print(f"\n{status_icon} Step {i+1}: {step['description']}")

            if step['status'] in [StepStatus.COMPLETED.value, StepStatus.FAILED.value]:
                print(f"   Result: {step['result']}")

                if step['duration'] is not None:
                    print(f"   Duration: {step['duration']:.2f} seconds")

        # Print artifacts if any
        if job.get('artifacts'):
            print("\nArtifacts:")
            for artifact in job['artifacts']:
                print(f"- {artifact['name']} ({artifact['type']}): {artifact['path']}")

        print("\n" + "=" * 80)

# Run the agent if executed directly
if __name__ == "__main__":
    agent = AgentRunner()
    agent.run_cli()
