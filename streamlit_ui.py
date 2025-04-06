# streamlit_ui.py

import streamlit as st
from models.llama3_runner import LlamaRunner
from memory import Memory
from tasks import TaskPlanner
import json
import traceback

llm = LlamaRunner(model_name="llama3")
memory = Memory()
planner = TaskPlanner(llm)

st.set_page_config(page_title="🧠 LLaMA Dev Agent", layout="wide")
st.title("🧠 LLaMA Dev Agent")

if "task_history" not in st.session_state:
    st.session_state.task_history = []

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# Debug mode toggle in sidebar
with st.sidebar:
    st.session_state.debug_mode = st.toggle("Debug Mode", st.session_state.debug_mode)

user_input = st.text_input(
    "Enter a dev task:",
    placeholder="e.g., create a Python script that scrapes Hacker News"
)

if st.button("Submit Task") and user_input:
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
            status.update(label="Planning task with LLaMA")
            plan = planner.plan_task(user_input, memory_context=similar)

            if not plan or len(plan) == 0:
                st.error("❌ Could not generate a plan. Try a simpler task or check logs.")
                if st.session_state.debug_mode:
                    st.error("Debug: LLM didn't return a parsable plan format")
            else:
                memory.log_plan(plan)
                st.session_state.task_history.append({"task": user_input, "plan": plan, "results": []})

                st.subheader("🧠 Generated Plan")
                for i, step in enumerate(plan, 1):
                    step_placeholder = st.empty()
                    step_placeholder.markdown(f"**Step {i}:** {step}")

                    status.update(label=f"Executing step {i}: {step}")
                    try:
                        result = planner.execute_step(step)
                        memory.log_result(step, result)

                        # Store result in session state
                        current_task = st.session_state.task_history[-1]
                        current_task["results"].append({"step": step, "result": result})

                        step_placeholder.markdown(f"**Step {i}:** {step}\n\n✅ **Result:** {result}")
                    except Exception as step_error:
                        error_msg = f"Error executing step: {str(step_error)}"
                        step_placeholder.markdown(f"**Step {i}:** {step}\n\n⚠️ **Error:** {error_msg}")
                        if st.session_state.debug_mode:
                            st.code(traceback.format_exc(), language="python")

                status.update(label="Task completed", state="complete")

        except Exception as e:
            error_msg = f"⚠️ An error occurred: {str(e)}"
            st.error(error_msg)
            if st.session_state.debug_mode:
                st.code(traceback.format_exc(), language="python")
            status.update(label="Task failed", state="error")

# Sidebar History
st.sidebar.title("🕘 Task History")

for i, entry in enumerate(reversed(st.session_state.task_history)):
    with st.sidebar.expander(f"Task {len(st.session_state.task_history) - i}: {entry['task'][:40]}..."):
        for j, step in enumerate(entry.get('plan', []), 1):
            result = next((r['result'] for r in entry.get('results', []) if r['step'] == step), None)
            if result:
                st.markdown(f"**Step {j}:** {step}\n\n✅ **Result:** {result}")
            else:
                st.markdown(f"**Step {j}:** {step}")
