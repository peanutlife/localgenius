# test_job_manager.py

import os
import shutil
import unittest
from jobs.job_manager import JobManager, JobStatus, StepStatus

class TestJobManager(unittest.TestCase):
    """Test cases for the JobManager class."""

    def setUp(self):
        """Set up a test environment before each test."""
        self.test_dir = "test_jobs"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
        self.job_manager = JobManager(jobs_dir=self.test_dir)

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_job(self):
        """Test creating a new job."""
        job_id = self.job_manager.create_job("Test task")
        self.assertIsNotNone(job_id)

        # Verify job exists
        job = self.job_manager.get_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job["task"], "Test task")
        self.assertEqual(job["status"], JobStatus.PENDING.value)

    def test_job_lifecycle(self):
        """Test the complete lifecycle of a job."""
        # Create job
        job_id = self.job_manager.create_job("Test lifecycle task")

        # Set plan
        plan = ["Step 1", "Step 2", "Step 3"]
        result = self.job_manager.set_job_plan(job_id, plan)
        self.assertTrue(result)

        # Verify plan was set
        job = self.job_manager.get_job(job_id)
        self.assertEqual(len(job["steps"]), 3)
        self.assertEqual(job["status"], JobStatus.RUNNING.value)

        # Execute first step
        self.job_manager.start_step(job_id, 0)
        self.job_manager.complete_step(job_id, 0, "Result of step 1")

        # Execute second step
        self.job_manager.start_step(job_id, 1)
        self.job_manager.complete_step(job_id, 1, "Result of step 2")

        # Execute third step
        self.job_manager.start_step(job_id, 2)
        self.job_manager.complete_step(job_id, 2, "Result of step 3")

        # Verify job is completed
        job = self.job_manager.get_job(job_id)
        self.assertEqual(job["status"], JobStatus.COMPLETED.value)

        # Verify all steps are completed
        all_completed = all(step["status"] == StepStatus.COMPLETED.value for step in job["steps"])
        self.assertTrue(all_completed)

    def test_job_with_failure(self):
        """Test a job with a failed step."""
        # Create job
        job_id = self.job_manager.create_job("Test failure task")

        # Set plan
        plan = ["Step 1", "Step 2", "Step 3"]
        self.job_manager.set_job_plan(job_id, plan)

        # Execute first step
        self.job_manager.start_step(job_id, 0)
        self.job_manager.complete_step(job_id, 0, "Result of step 1")

        # Execute second step with failure
        self.job_manager.start_step(job_id, 1)
        self.job_manager.complete_step(job_id, 1, "Failed", StepStatus.FAILED)

        # Execute third step
        self.job_manager.start_step(job_id, 2)
        self.job_manager.complete_step(job_id, 2, "Result of step 3")

        # Verify job is failed
        job = self.job_manager.get_job(job_id)
        self.assertEqual(job["status"], JobStatus.FAILED.value)

    def test_list_jobs(self):
        """Test listing jobs."""
        # Create several jobs
        job_ids = []
        for i in range(5):
            job_id = self.job_manager.create_job(f"Test task {i}")
            job_ids.append(job_id)

        # List all jobs
        jobs = self.job_manager.list_jobs()
        self.assertEqual(len(jobs), 5)

        # Test with limit
        jobs = self.job_manager.list_jobs(limit=3)
        self.assertEqual(len(jobs), 3)

        # Update status of some jobs
        self.job_manager.update_job_status(job_ids[0], JobStatus.RUNNING)
        self.job_manager.update_job_status(job_ids[1], JobStatus.COMPLETED)

        # Filter by status
        running_jobs = self.job_manager.list_jobs(status=JobStatus.RUNNING)
        self.assertEqual(len(running_jobs), 1)
        self.assertEqual(running_jobs[0]["id"], job_ids[0])

    def test_artifacts(self):
        """Test adding artifacts to a job."""
        job_id = self.job_manager.create_job("Test artifacts")

        # Add artifacts
        result = self.job_manager.add_artifact(
            job_id,
            "file",
            "test.py",
            "workspace/test.py",
            {"size": 1024}
        )
        self.assertTrue(result)

        # Verify artifact was added
        job = self.job_manager.get_job(job_id)
        self.assertEqual(len(job["artifacts"]), 1)
        self.assertEqual(job["artifacts"][0]["name"], "test.py")
        self.assertEqual(job["artifacts"][0]["metadata"]["size"], 1024)

    def test_delete_job(self):
        """Test deleting a job."""
        job_id = self.job_manager.create_job("Test delete")

        # Delete job
        result = self.job_manager.delete_job(job_id)
        self.assertTrue(result)

        # Verify job is gone
        job = self.job_manager.get_job(job_id)
        self.assertIsNone(job)

        # Verify job file is gone
        job_file = os.path.join(self.test_dir, f"{job_id}.json")
        self.assertFalse(os.path.exists(job_file))

if __name__ == "__main__":
    unittest.main()
