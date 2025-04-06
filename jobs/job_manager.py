# jobs/job_manager.py

import os
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

class JobStatus(Enum):
    PENDING = "pending"        # Job created but not started
    PLANNING = "planning"      # Planning in progress
    RUNNING = "running"        # Executing steps
    PAUSED = "paused"          # Execution paused
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed during execution
    ABORTED = "aborted"        # Manually aborted

class StepStatus(Enum):
    PENDING = "pending"        # Step not started
    RUNNING = "running"        # Step in progress
    COMPLETED = "completed"    # Step completed successfully
    FAILED = "failed"          # Step failed

class JobManager:
    def __init__(self, jobs_dir="workspace/jobs"):
        """Initialize the JobManager with the specified jobs directory."""
        self.jobs_dir = jobs_dir
        os.makedirs(self.jobs_dir, exist_ok=True)

        # Maintain an in-memory index of jobs
        self.jobs_index = {}
        self._load_jobs_index()

    def _load_jobs_index(self):
        """Load all jobs from the jobs directory into the in-memory index."""
        job_files = [f for f in os.listdir(self.jobs_dir) if f.endswith('.json')]

        for job_file in job_files:
            try:
                with open(os.path.join(self.jobs_dir, job_file), 'r') as f:
                    job_data = json.load(f)
                    job_id = job_data.get('id')
                    if job_id:
                        self.jobs_index[job_id] = {
                            'id': job_id,
                            'task': job_data.get('task'),
                            'status': job_data.get('status'),
                            'created_at': job_data.get('created_at'),
                            'updated_at': job_data.get('updated_at'),
                            'file': job_file
                        }
            except Exception as e:
                print(f"Error loading job file {job_file}: {e}")

    def create_job(self, task: str) -> str:
        """
        Create a new job with the given task description.

        Args:
            task: The description of the task to be performed

        Returns:
            The ID of the newly created job
        """
        job_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        job_data = {
            'id': job_id,
            'task': task,
            'status': JobStatus.PENDING.value,
            'created_at': timestamp,
            'updated_at': timestamp,
            'plan': [],
            'steps': [],
            'memory_context': [],
            'artifacts': [],
            'metadata': {}
        }

        # Save to index
        self.jobs_index[job_id] = {
            'id': job_id,
            'task': task,
            'status': JobStatus.PENDING.value,
            'created_at': timestamp,
            'updated_at': timestamp,
            'file': f"{job_id}.json"
        }

        # Save to file
        self._save_job(job_id, job_data)

        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the full details of a specific job.

        Args:
            job_id: The ID of the job to retrieve

        Returns:
            The job data as a dictionary, or None if not found
        """
        if job_id not in self.jobs_index:
            return None

        job_file = self.jobs_index[job_id]['file']
        try:
            with open(os.path.join(self.jobs_dir, job_file), 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading job {job_id}: {e}")
            return None

    def list_jobs(self, limit: int = 20, status: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """
        List jobs, optionally filtered by status.

        Args:
            limit: Maximum number of jobs to return
            status: Filter by status (optional)

        Returns:
            List of job summary dictionaries
        """
        jobs = list(self.jobs_index.values())

        # Apply status filter if provided
        if status:
            status_value = status.value if isinstance(status, JobStatus) else status
            jobs = [job for job in jobs if job['status'] == status_value]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return jobs[:limit]

    def update_job_status(self, job_id: str, status: JobStatus) -> bool:
        """
        Update the status of a job.

        Args:
            job_id: The ID of the job to update
            status: The new status to set

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return False

        job_data['status'] = status.value
        job_data['updated_at'] = datetime.now().isoformat()

        # Update in-memory index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['status'] = status.value
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def set_job_plan(self, job_id: str, plan: List[str]) -> bool:
        """
        Set the plan for a job.

        Args:
            job_id: The ID of the job to update
            plan: List of step descriptions

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return False

        job_data['plan'] = plan
        job_data['updated_at'] = datetime.now().isoformat()

        # Initialize steps with pending status
        job_data['steps'] = [
            {
                'index': i,
                'description': step,
                'status': StepStatus.PENDING.value,
                'result': None,
                'started_at': None,
                'completed_at': None,
                'duration': None
            }
            for i, step in enumerate(plan)
        ]

        # Update job status to reflect we now have a plan
        job_data['status'] = JobStatus.RUNNING.value

        # Update in-memory index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['status'] = job_data['status']
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def start_step(self, job_id: str, step_index: int) -> bool:
        """
        Mark a step as starting execution.

        Args:
            job_id: The ID of the job
            step_index: Index of the step to update

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data or 'steps' not in job_data or step_index >= len(job_data['steps']):
            return False

        job_data['steps'][step_index]['status'] = StepStatus.RUNNING.value
        job_data['steps'][step_index]['started_at'] = datetime.now().isoformat()
        job_data['updated_at'] = datetime.now().isoformat()

        # Update in-memory index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def complete_step(self, job_id: str, step_index: int, result: str, status: StepStatus = StepStatus.COMPLETED) -> bool:
        """
        Mark a step as completed with results.

        Args:
            job_id: The ID of the job
            step_index: Index of the step to update
            result: Result of the step execution
            status: Status to set for the step (completed or failed)

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data or 'steps' not in job_data or step_index >= len(job_data['steps']):
            return False

        timestamp = datetime.now().isoformat()

        # Calculate duration
        started_at = job_data['steps'][step_index].get('started_at')
        if started_at:
            started_time = datetime.fromisoformat(started_at)
            completed_time = datetime.now()
            duration_seconds = (completed_time - started_time).total_seconds()
        else:
            duration_seconds = None

        job_data['steps'][step_index].update({
            'status': status.value,
            'result': result,
            'completed_at': timestamp,
            'duration': duration_seconds
        })

        job_data['updated_at'] = timestamp

        # Check if all steps are completed
        all_completed = all(step['status'] in [StepStatus.COMPLETED.value, StepStatus.FAILED.value]
                           for step in job_data['steps'])

        any_failed = any(step['status'] == StepStatus.FAILED.value for step in job_data['steps'])

        # Update job status if needed
        if all_completed:
            job_data['status'] = JobStatus.FAILED.value if any_failed else JobStatus.COMPLETED.value

            # Update in-memory index
            if job_id in self.jobs_index:
                self.jobs_index[job_id]['status'] = job_data['status']

        # Always update timestamp in index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def add_artifact(self, job_id: str, artifact_type: str, name: str, path: str, metadata: Dict = None) -> bool:
        """
        Add an artifact (file or output) to a job.

        Args:
            job_id: The ID of the job
            artifact_type: Type of artifact (file, output, etc.)
            name: Name of the artifact
            path: Path to the artifact
            metadata: Additional metadata about the artifact

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return False

        artifact = {
            'type': artifact_type,
            'name': name,
            'path': path,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        job_data['artifacts'].append(artifact)
        job_data['updated_at'] = datetime.now().isoformat()

        # Update in-memory index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def set_memory_context(self, job_id: str, memory_context: List[str]) -> bool:
        """
        Set the memory context used for a job.

        Args:
            job_id: The ID of the job
            memory_context: List of memory items used as context

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return False

        job_data['memory_context'] = memory_context
        job_data['updated_at'] = datetime.now().isoformat()

        # Update in-memory index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def abort_job(self, job_id: str) -> bool:
        """
        Abort a running job.

        Args:
            job_id: The ID of the job to abort

        Returns:
            True if successful, False otherwise
        """
        return self.update_job_status(job_id, JobStatus.ABORTED)

    def pause_job(self, job_id: str) -> bool:
        """
        Pause a running job.

        Args:
            job_id: The ID of the job to pause

        Returns:
            True if successful, False otherwise
        """
        return self.update_job_status(job_id, JobStatus.PAUSED)

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job.

        Args:
            job_id: The ID of the job to resume

        Returns:
            True if successful, False otherwise
        """
        return self.update_job_status(job_id, JobStatus.RUNNING)

    def get_next_pending_step(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the next pending step for a job.

        Args:
            job_id: The ID of the job

        Returns:
            Dictionary with step details or None if no pending steps
        """
        job_data = self.get_job(job_id)
        if not job_data or 'steps' not in job_data:
            return None

        for step in job_data['steps']:
            if step['status'] == StepStatus.PENDING.value:
                return step

        return None

    def set_metadata(self, job_id: str, key: str, value: Any) -> bool:
        """
        Set a metadata value for a job.

        Args:
            job_id: The ID of the job
            key: Metadata key
            value: Metadata value

        Returns:
            True if successful, False otherwise
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return False

        if 'metadata' not in job_data:
            job_data['metadata'] = {}

        job_data['metadata'][key] = value
        job_data['updated_at'] = datetime.now().isoformat()

        # Update in-memory index
        if job_id in self.jobs_index:
            self.jobs_index[job_id]['updated_at'] = job_data['updated_at']

        return self._save_job(job_id, job_data)

    def _save_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """
        Save job data to file.

        Args:
            job_id: The ID of the job
            job_data: The job data to save

        Returns:
            True if successful, False otherwise
        """
        job_file = f"{job_id}.json"
        job_path = os.path.join(self.jobs_dir, job_file)

        try:
            with open(job_path, 'w') as f:
                json.dump(job_data, f, indent=2)

            # Update file name in index if needed
            if job_id in self.jobs_index and self.jobs_index[job_id]['file'] != job_file:
                self.jobs_index[job_id]['file'] = job_file

            return True
        except Exception as e:
            print(f"Error saving job {job_id}: {e}")
            return False

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: The ID of the job to delete

        Returns:
            True if successful, False otherwise
        """
        if job_id not in self.jobs_index:
            return False

        job_file = self.jobs_index[job_id]['file']
        job_path = os.path.join(self.jobs_dir, job_file)

        try:
            if os.path.exists(job_path):
                os.remove(job_path)

            # Remove from index
            del self.jobs_index[job_id]
            return True
        except Exception as e:
            print(f"Error deleting job {job_id}: {e}")
            return False
