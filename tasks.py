# tasks.py

from tools.exec import run_code
from tools.file_ops import write_file
import re

class TaskPlanner:
    def __init__(self, llm):
        self.llm = llm

#     def plan_task(self, task_desc):
#         prompt = f"""
# You are a helpful agent. Break down the following task into 3–5 clear, executable steps:\n\nTask: {task_desc}
# Steps:
# 1.
# """
#         output = self.llm.run(prompt)
#         steps = self._parse_steps(output)
#         return steps

    def plan_task(self, task_desc, memory_context=None):
        context = "\n".join(memory_context or [])
        prompt = f"""
    You are a helpful developer assistant.

    Here is relevant memory from past tasks:
    {context}

    Now break down this new task into 3–5 executable steps:
    Task: {task_desc}
    Steps:
    1.
    """
        output = self.llm.run(prompt)
        return self._parse_steps(output)

    def _parse_steps(self, raw):
        lines = raw.strip().splitlines()
        steps = [line.split(".", 1)[1].strip() for line in lines if re.match(r"^\d+\.", line)]
        return steps

    def execute_step(self, step):
        # If it's a code step, ask the LLM for code and run it
        if "create" in step.lower() or "write" in step.lower() or "generate code" in step.lower():
            code = self.llm.run(f"Generate Python code to: {step}\nOnly return code, no explanation.")
            file_name = f"workspace/{step.replace(' ', '_')[:40]}.py"
            write_file(file_name, code)
            return f"Code written to {file_name}"
        elif "run" in step.lower() or "execute" in step.lower():
            code = self.llm.run(f"Write a script to: {step}\nOnly return code.")
            return run_code(code)
        else:
            return self.llm.run(f"How would you: {step}")
