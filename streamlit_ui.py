# streamlit_ui.py

import streamlit as st
from models.llama3_runner import LlamaRunner
from memory import Memory
from tasks import TaskPlanner
from jobs.job_manager import JobManager, JobStatus, StepStatus
from tools import get_registry
import json
import traceback
import os
import time
from datetime import datetime

# Initialize components
llm = LlamaRunner(model_name="llama3")
memory = Memory()
job_manager = JobManager()
tools = get_registry()
planner = TaskPlanner(llm)

# Page Configuration
st.set_page_config(
    page_title="🧠 LocalGenius",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Tasks"
if "current_job_id" not in st.session_state:
    st.session_state.current_job_id = None
if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False
if "file_list" not in st.session_state:
    st.session_state.file_list = []
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None
if "expanded_jobs" not in st.session_state:
    st.session_state.expanded_jobs = set()
if "_switch_to_tab" not in st.session_state:
    st.session_state._switch_to_tab = None

# Handle tab switching before widgets are created
if st.session_state._switch_to_tab is not None:
    st.session_state.active_tab = st.session_state._switch_to_tab
    st.session_state._switch_to_tab = None

# Helper Functions
def refresh_file_list():
    """Refresh the list of files in the workspace directory"""
    workspace_dir = "workspace"
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)

    files = [f for f in os.listdir(workspace_dir) if os.path.isfile(os.path.join(workspace_dir, f))]
    st.session_state.file_list = sorted(files)

def format_time(iso_time):
    """Format ISO timestamp to a readable format"""
    if not iso_time:
        return ""
    try:
        dt = datetime.fromisoformat(iso_time)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_time

def toggle_expand_job(job_id):
    """Toggle the expanded state of a job in the sidebar"""
    if job_id in st.session_state.expanded_jobs:
        st.session_state.expanded_jobs.remove(job_id)
    else:
        st.session_state.expanded_jobs.add(job_id)

# Sidebar content
with st.sidebar:
    st.title("🧠 LocalGenius")

    # Tab Selection
    selected_tab = st.radio(
        "Navigation",
        ["Tasks", "Jobs", "Files", "Tools", "Settings"],
        key="active_tab"
    )

    # Jobs List (always visible for quick access)
    st.markdown("---")
    st.subheader("Recent Jobs")

    jobs = job_manager.list_jobs(limit=5)
    if not jobs:
        st.info("No jobs found")
    else:
        for job in jobs:
            status_icon = "✅" if job['status'] == JobStatus.COMPLETED.value else "❌" if job['status'] == JobStatus.FAILED.value else "⏳" if job['status'] == JobStatus.RUNNING.value else "⏸️"
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{status_icon} {job['task'][:30]}{'...' if len(job['task']) > 30 else ''}")
            with col2:
                if st.button("View", key=f"sidebar_{job['id']}"):
                    st.session_state.current_job_id = job['id']
                    # Use the switch_to_tab variable instead of directly modifying active_tab
                    st.session_state._switch_to_tab = "Jobs"
                    st.rerun()

    # Debug mode toggle in sidebar
    st.markdown("---")
    debug_toggle = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    if debug_toggle != st.session_state.debug_mode:
        st.session_state.debug_mode = debug_toggle
        st.rerun()

# Main content
if st.session_state.active_tab == "Tasks":
    st.title("Create New Task")

    with st.form(key="task_form"):
        user_input = st.text_area(
            "Enter a dev task:",
            placeholder="e.g., create a Python script that scrapes Hacker News",
            height=100
        )

        submit_button = st.form_submit_button("Submit Task")

    if submit_button and user_input:
        with st.status("Processing task...") as status:
            status.update(label="Logging task to memory")
            memory.log_task(user_input)

            status.update(label="Searching similar tasks")
            similar = memory.search_memory(user_input)

            if similar:
                st.subheader("🔍 Similar Tasks in Memory")
                for i, match in enumerate(similar, 1):
                    st.markdown(f"{i}. {match[:200]}{'...' if len(match) > 200 else ''}")

            try:
                # Create a new job
                job_id = job_manager.create_job(user_input)
                st.session_state.current_job_id = job_id

                # Update job status to planning
                job_manager.update_job_status(job_id, JobStatus.PLANNING)

                # Save memory context to job if available
                if similar:
                    job_manager.set_memory_context(job_id, similar)

                status.update(label="Planning task with LLaMA")
                plan = planner.plan_task(user_input, memory_context=similar)

                if not plan or len(plan) == 0:
                    st.error("❌ Could not generate a plan. Try a simpler task or check logs.")
                    if st.session_state.debug_mode:
                        st.error("Debug: LLM didn't return a parsable plan format")
                else:
                    memory.log_plan(plan)

                    # Save plan to job
                    job_manager.set_job_plan(job_id, plan)

                    # Display the plan
                    st.subheader("🧠 Generated Plan")
                    for i, step in enumerate(plan, 1):
                        step_placeholder = st.empty()
                        step_placeholder.markdown(f"**Step {i}:** {step}")

                        status.update(label=f"Executing step {i}: {step}")

                        # Mark step as running
                        job_manager.start_step(job_id, i-1)

                        try:
                            result = planner.execute_step(step, i-1)
                            memory.log_result(step, result)

                            # Mark step as completed
                            job_manager.complete_step(job_id, i-1, result)

                            step_placeholder.markdown(f"**Step {i}:** {step}\n\n✅ **Result:** {result}")
                        except Exception as step_error:
                            error_msg = f"Error executing step: {str(step_error)}"
                            step_placeholder.markdown(f"**Step {i}:** {step}\n\n⚠️ **Error:** {error_msg}")

                            # Mark step as failed
                            job_manager.complete_step(job_id, i-1, error_msg, StepStatus.FAILED)

                            if st.session_state.debug_mode:
                                st.code(traceback.format_exc(), language="python")

                    status.update(label="Task completed", state="complete")

                    # Refresh file list
                    refresh_file_list()

            except Exception as e:
                error_msg = f"⚠️ An error occurred: {str(e)}"
                st.error(error_msg)
                if st.session_state.debug_mode:
                    st.code(traceback.format_exc(), language="python")
                status.update(label="Task failed", state="error")

elif st.session_state.active_tab == "Jobs":
    st.title("Job Management")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Jobs List")

        status_filter = st.selectbox(
            "Filter by status",
            ["All"] + [status.value for status in JobStatus],
            index=0
        )

        limit = st.slider("Number of jobs to show", min_value=5, max_value=50, value=20, step=5)

        if st.button("Refresh Jobs"):
            st.rerun()

        # Get jobs
        filtered_status = None if status_filter == "All" else status_filter
        jobs = job_manager.list_jobs(limit=limit, status=filtered_status)

        if not jobs:
            st.info("No jobs found matching the criteria.")
        else:
            # Create a dataframe-like display
            for job in jobs:
                col_job, col_status, col_date, col_actions = st.columns([3, 1, 2, 1])

                with col_job:
                    st.markdown(f"**{job['task'][:50]}{'...' if len(job['task']) > 50 else ''}**")

                with col_status:
                    status_color = "green" if job['status'] == JobStatus.COMPLETED.value else "red" if job['status'] == JobStatus.FAILED.value else "blue"
                    st.markdown(f"<span style='color:{status_color}'>{job['status']}</span>", unsafe_allow_html=True)

                with col_date:
                    st.text(format_time(job.get('created_at', '')))

                with col_actions:
                    if st.button("View", key=f"view_job_{job['id']}"):
                        st.session_state.current_job_id = job['id']
                        st.rerun()

                st.markdown("---")

    with col2:
        st.subheader("Job Details")

        if st.session_state.current_job_id:
            job = job_manager.get_job(st.session_state.current_job_id)
            if job:
                st.markdown(f"**ID:** {job['id']}")
                st.markdown(f"**Status:** {job['status']}")
                st.markdown(f"**Task:** {job['task']}")
                st.markdown(f"**Created:** {format_time(job.get('created_at', ''))}")
                st.markdown(f"**Updated:** {format_time(job.get('updated_at', ''))}")

                # Action buttons
                col_a, col_b = st.columns(2)
                with col_a:
                    if job['status'] in [JobStatus.PAUSED.value, JobStatus.RUNNING.value]:
                        if st.button("Resume Job"):
                            st.info("Resuming job...")
                            planner.current_job_id = job['id']
                            job_manager.update_job_status(job['id'], JobStatus.RUNNING)

                            # Find the first incomplete step
                            for step_index, step in enumerate(job['steps']):
                                if step['status'] in [StepStatus.PENDING.value, StepStatus.RUNNING.value]:
                                    # Execute the step
                                    try:
                                        job_manager.start_step(job['id'], step_index)
                                        result = planner.execute_step(step['description'], step_index)
                                        job_manager.complete_step(job['id'], step_index, result)

                                        # Refresh job details
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error executing step: {str(e)}")
                                        job_manager.complete_step(job['id'], step_index, str(e), StepStatus.FAILED)
                                        st.rerun()
                                    break

                with col_b:
                    if job['status'] == JobStatus.RUNNING.value:
                        if st.button("Abort Job"):
                            job_manager.abort_job(job['id'])
                            st.rerun()

                # Plan
                with st.expander("Plan", expanded=True):
                    for i, step in enumerate(job.get('plan', []), 1):
                        st.markdown(f"{i}. {step}")

                # Steps with results
                with st.expander("Execution Steps", expanded=True):
                    for i, step in enumerate(job.get('steps', []), 1):
                        status_icon = "✅" if step['status'] == StepStatus.COMPLETED.value else "❌" if step['status'] == StepStatus.FAILED.value else "⏳" if step['status'] == StepStatus.RUNNING.value else "⏸️"
                        st.markdown(f"{status_icon} **Step {i}:** {step['description']}")

                        if step['status'] in [StepStatus.COMPLETED.value, StepStatus.FAILED.value]:
                            st.markdown(f"**Result:** {step['result']}")

                            if step['duration'] is not None:
                                st.markdown(f"**Duration:** {step['duration']:.2f} seconds")

                        # Step retry button
                        if step['status'] == StepStatus.FAILED.value:
                            retry_btn_key = f"retry_{step['index']}_{job['id']}"  # Make sure key is unique
                            if st.button(f"Retry Step {i}", key=retry_btn_key):
                                try:
                                    st.info(f"Retrying step {i}...")
                                    planner.current_job_id = job['id']
                                    job_manager.start_step(job['id'], step['index'])
                                    result = planner.execute_step(step['description'], step['index'])
                                    job_manager.complete_step(job['id'], step['index'], result)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error retrying step: {str(e)}")
                                    job_manager.complete_step(job['id'], step['index'], str(e), StepStatus.FAILED)
                                    st.rerun()

                # Memory context
                if job.get('memory_context'):
                    with st.expander("Memory Context", expanded=False):
                        for i, context in enumerate(job['memory_context'], 1):
                            st.markdown(f"{i}. {context}")

                # Artifacts
                if job.get('artifacts'):
                    with st.expander("Artifacts", expanded=False):
                        for artifact in job['artifacts']:
                            st.markdown(f"**{artifact['name']}** ({artifact['type']}): {artifact['path']}")
            else:
                st.info("Select a job to view details")
        else:
            st.info("Select a job to view details")

elif st.session_state.active_tab == "Files":
    st.title("File Management")

    # Add file upload capability
    uploaded_file = st.file_uploader("Upload a file to workspace directory", type=None)
    if uploaded_file is not None:
        try:
            # Ensure workspace directory exists
            if not os.path.exists("workspace"):
                os.makedirs("workspace")

            # Save uploaded file to workspace directory
            file_path = os.path.join("workspace", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File uploaded successfully: {uploaded_file.name}")

            # Refresh file list
            refresh_file_list()
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")

    # Refresh file list
    refresh_file_list()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Files")

        if not st.session_state.file_list:
            st.info("No files found in workspace directory")
        else:
            for file in st.session_state.file_list:
                file_btn_key = f"file_{file}"  # Make key unique
                if st.button(file, key=file_btn_key):
                    st.session_state.selected_file = file
                    st.rerun()

    with col2:
        st.subheader("File Content")

        if st.session_state.selected_file:
            file_path = os.path.join("workspace", st.session_state.selected_file)

            # Get file extension
            file_ext = os.path.splitext(st.session_state.selected_file)[1].lower()

            try:
                with open(file_path, "r") as f:
                    content = f.read()

                # Display file content with appropriate highlighting
                if file_ext in [".py", ".js", ".html", ".css", ".json"]:
                    st.code(content, language=file_ext[1:])
                else:
                    st.text(content)

                # File operations
                col_a, col_b = st.columns(2)
                with col_a:
                    edit_key = f"edit_{st.session_state.selected_file}"
                    if st.button("Edit", key=edit_key):
                        # Enable editing in a text area
                        edited_content = st.text_area(
                            "Edit file content",
                            value=content,
                            height=400
                        )

                        save_key = f"save_{st.session_state.selected_file}"
                        if st.button("Save Changes", key=save_key):
                            try:
                                with open(file_path, "w") as f:
                                    f.write(edited_content)
                                st.success(f"File saved: {file_path}")
                            except Exception as e:
                                st.error(f"Error saving file: {str(e)}")

                with col_b:
                    delete_key = f"delete_{st.session_state.selected_file}"
                    if st.button("Delete", key=delete_key):
                        warning_key = f"warning_{st.session_state.selected_file}"
                        st.warning(f"Are you sure you want to delete {st.session_state.selected_file}?", icon="⚠️")

                        confirm_key = f"confirm_{st.session_state.selected_file}"
                        if st.button("Confirm Delete", key=confirm_key):
                            try:
                                os.remove(file_path)
                                st.success(f"File deleted: {file_path}")
                                st.session_state.selected_file = None
                                refresh_file_list()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting file: {str(e)}")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        else:
            st.info("Select a file to view its content")

elif st.session_state.active_tab == "Tools":
    st.title("Tools Registry")

    # Get all available tools
    tool_list = tools.list_tools()

    # Group tools by category
    tool_categories = {}
    for name, description in tool_list.items():
        # Extract category from tool name
        if "_" in name:
            category = name.split("_")[0]
        else:
            category = "general"

        if category not in tool_categories:
            tool_categories[category] = []

        tool_categories[category].append({
            "name": name,
            "description": description
        })

    # Display tools by category
    for category, tools_list in tool_categories.items():
        with st.expander(f"{category.title()} Tools", expanded=True):
            for tool in tools_list:
                st.markdown(f"**{tool['name']}**: {tool['description']}")

    # Tool Testing Section
    st.subheader("Test Tools")
    st.markdown("Select a tool to test its functionality:")

    selected_tool = st.selectbox("Select Tool", options=list(tool_list.keys()))

    if selected_tool:
        st.markdown(f"**Description**: {tool_list[selected_tool]}")

        # Dynamic form based on tool name patterns
        with st.form(key="tool_test_form"):
            params = {}

            # Special case for list_files which expects 'directory' instead of 'path'
            if selected_tool == "list_files":
                params["directory"] = st.text_input("Directory Path", value=".")
            # File path parameter for most file operations
            elif "file" in selected_tool or "read" in selected_tool or "write" in selected_tool:
                params["path"] = st.text_input("File Path", value="workspace/")

            # Content parameter for write operations
            if "write" in selected_tool:
                params["content"] = st.text_area("Content")

            # Query parameter for database operations
            if "query" in selected_tool or selected_tool == "execute_query":
                params["query"] = st.text_area("SQL Query")
                params["db_path"] = st.text_input("Database Path", value="workspace/database.db")

            # URL parameter for web tools
            if "url" in selected_tool or "fetch" in selected_tool or "download" in selected_tool:
                params["url"] = st.text_input("URL")

            # Command parameter for shell operations
            if "shell" in selected_tool or selected_tool == "run_shell":
                params["command"] = st.text_input("Shell Command")

            # Code parameter for code execution
            if "code" in selected_tool or selected_tool == "run_code":
                params["code"] = st.text_area("Code")

            # Submit button
            submit_test = st.form_submit_button("Run Tool")

        if submit_test:
            with st.status("Executing tool..."):
                try:
                    # Execute the tool with parameters
                    result = tools.execute(selected_tool, **params)

                    # Display result
                    st.subheader("Result")

                    # Format result based on type
                    if isinstance(result, dict):
                        st.json(result)
                    elif isinstance(result, list):
                        for item in result:
                            st.write(item)
                    elif isinstance(result, str):
                        st.text(result)
                    else:
                        st.write(result)

                    # Refresh file list if this was a file operation
                    if any(op in selected_tool for op in ["file", "write", "create"]):
                        refresh_file_list()

                except Exception as e:
                    st.error(f"Error executing tool: {str(e)}")
                    if st.session_state.debug_mode:
                        st.code(traceback.format_exc(), language="python")

elif st.session_state.active_tab == "Settings":
    st.title("Settings")

    # Debug Mode
    st.subheader("Debug Options")
    debug_toggle = st.toggle("Debug Mode", st.session_state.debug_mode,
                         help="Enable detailed error messages and execution logs")
    if debug_toggle != st.session_state.debug_mode:
        st.session_state.debug_mode = debug_toggle
        st.rerun()

    # LLM Options
    st.subheader("LLM Configuration")
    llm_model = st.selectbox(
        "LLM Model",
        ["llama3:8b", "llama3:70b", "mistral:7b"],
        index=0
    )

    if st.button("Update LLM Model"):
        st.info(f"Switching to model: {llm_model}...")
        # In a real implementation, this would update the LLM instance
        st.success(f"Model updated to {llm_model}")

    # Memory Management
    st.subheader("Memory Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Clear Memory Cache"):
            # This would clear the vector database in a real implementation
            st.warning("This will delete all stored memories. Are you sure?")
            confirm_clear = st.button("Confirm Clear Memory", key="confirm_clear_memory")
            if confirm_clear:
                st.info("Clearing memory cache...")
                # memory.clear_cache()  # You would need to implement this
                st.success("Memory cache cleared")

    with col2:
        if st.button("Export Memory"):
            st.info("Exporting memory to file...")
            # In a real implementation, this would export the memory database
            st.download_button(
                label="Download Memory Export",
                data="Sample memory export",  # Replace with real export
                file_name="memory_export.json",
                mime="application/json"
            )

    # Job Cleanup
    st.subheader("Job Management")

    job_retention = st.slider(
        "Job Retention Period (days)",
        min_value=1,
        max_value=30,
        value=7,
        help="Jobs older than this will be automatically deleted"
    )

    if st.button("Clean Up Jobs"):
        st.warning("This will delete completed jobs. Are you sure?")
        confirm_cleanup = st.button("Confirm Cleanup", key="confirm_job_cleanup")
        if confirm_cleanup:
            # This would delete old jobs in a real implementation
            st.info("Cleaning up old jobs...")
            # job_manager.cleanup_jobs(days=job_retention)
            st.success("Old jobs cleaned up")

    # Workspace Management
    st.subheader("Workspace Management")

    if st.button("Clean Workspace"):
        st.warning("This will delete temporary files from the workspace. Are you sure?")
        confirm_workspace = st.button("Confirm Workspace Cleanup", key="confirm_workspace_cleanup")
        if confirm_workspace:
            # This would clean up temporary files in a real implementation
            st.info("Cleaning up workspace...")
            # Implement workspace cleanup logic
            st.success("Workspace cleaned")
