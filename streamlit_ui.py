# streamlit_ui.py

import streamlit as st
from models.llama3_runner import LlamaRunner
from memory import Memory
from tasks import TaskPlanner
import json

llm = LlamaRunner(model_name="llama3")
memory = Memory()
planner = TaskPlanner(llm)

st.set_page_config(page_title="🧠 LLaMA Dev Agent", layout="wide")
st.title("🧠 LLaMA Dev Agent")

if "task_history" not in st.session_state:
    st.session_state.task_history = []

user_input = st.text_input(
    "Enter a dev task:",
    placeholder="e.g., create a Python script that scrapes Hacker News"
)

if st.button("Submit Task") and user_input:
    memory.log_task(user_input)
    similar = memory.search_memory(user_input)

    if similar:
        st.subheader("🔍 Similar Tasks in Memory")
        for i, match in enumerate(similar, 1):
            st.markdown(f"{i}. {match[:200]}{'...' if len(match) > 200 else ''}")

    try:
        with st.spinner("🛠️ Planning task..."):
            plan = planner.plan_task(user_input, memory_context=similar)
            if not plan:
                st.error("❌ Could not generate a plan. Try a simpler task or check logs.")
            else:
                memory.log_plan(plan)
                st.session_state.task_history.append({"task": user_input, "plan": plan})

                st.subheader("🧠 Generated Plan")
                for i, step in enumerate(plan, 1):
                    st.markdown(f"**Step {i}:** {step}")
                    result = planner.execute_step(step)
                    memory.log_result(step, result)
                    st.markdown(f"✅ **Result:** {result}")
    except Exception as e:
        st.error(f"⚠️ An error occurred: {e}")

# Sidebar History
st.sidebar.title("🕘 Task History")
for i, entry in enumerate(reversed(st.session_state.task_history)):
    with st.sidebar.expander(f"Task {len(st.session_state.task_history) - i}: {entry['task'][:40]}..."):
        for j, step in enumerate(entry['plan'], 1):
            st.markdown(f"**Step {j}:** {step}")
