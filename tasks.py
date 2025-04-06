# tasks.py

from tools.exec import run_code
from tools.file_ops import write_file
import re

class TaskPlanner:
    def __init__(self, llm):
        self.llm = llm

    def plan_task(self, task_desc, memory_context=None):
        context = "\n".join(memory_context or [])
        prompt = f"""
You are a helpful developer assistant that writes Python code to accomplish tasks.

Here is relevant memory from past tasks:
{context}

Break down this task into 3-5 executable steps.
IMPORTANT: Focus on coding steps - each step should involve writing or running code.
Avoid planning/research steps that don't involve coding.

Your response MUST follow this format, with each step on a new line starting with a number followed by a period:
1. First coding step (e.g., "Write a script to...")
2. Second coding step (e.g., "Implement a function that...")
3. Third coding step (e.g., "Create a loop to...")

Task: {task_desc}
Steps:
1.
"""
        output = self.llm.run(prompt)
        print(f"LLM Raw Response for planning: {output[:100]}...")  # Debug logging

        steps = self._parse_steps(output)
        if not steps:
            print("Warning: Could not parse steps from LLM output. Raw output:")
            print(output)
        return steps

    def _parse_steps(self, raw):
        if not raw or not raw.strip():
            return []

        lines = raw.strip().splitlines()
        steps = []

        # Try standard numbered format (e.g., "1. Step description")
        numbered_steps = [line.split(".", 1)[1].strip() for line in lines
                         if re.match(r"^\d+\.", line) and "." in line]
        if numbered_steps:
            return numbered_steps

        # Try alternate formats (e.g., "Step 1: Description")
        for line in lines:
            match = re.search(r"step\s*\d+[:\)]\s*(.*)", line, re.IGNORECASE)
            if match:
                steps.append(match.group(1).strip())

        # If nothing found, try to salvage any lines that might be steps
        if not steps:
            # Look for lines that seem to be instructions
            for line in lines:
                # Skip short lines or headers
                if len(line.strip()) > 10 and not line.strip().endswith(':') and not line.strip().startswith('#'):
                    # Skip lines that are clearly not steps
                    if not any(word in line.lower() for word in ['reason', 'explanation', 'note:']):
                        steps.append(line.strip())

            # Limit to at most 5 steps
            steps = steps[:5]

        return steps

    def execute_step(self, step):
        prompt = f"""
You are a Python developer tasked with implementing code for the following step:
"{step}"

Write EXECUTABLE Python code to accomplish this task.
- Include all necessary imports
- Use requests and BeautifulSoup if web scraping is involved
- Use proper error handling with try/except
- Use functions appropriately
- Include sample code that calls your functions
- ONLY provide working Python code without any explanations

CODE:
```python
"""
        code_response = self.llm.run(prompt)

        # Clean up code - extract from markdown blocks if present
        if "```" in code_response:
            code_blocks = re.findall(r"```(?:python)?\n(.*?)```", code_response, re.DOTALL)
            if code_blocks:
                code = code_blocks[0]
            else:
                code = code_response
        else:
            code = code_response

        # Determine if we should write to file or execute directly
        if any(keyword in step.lower() for keyword in ["create", "write", "implement", "develop"]):
            # Generate a descriptive filename
            words = re.findall(r'\w+', step.lower())
            filename = '_'.join(words[:5])  # First 5 words for filename
            file_name = f"workspace/{filename}.py"
            write_file(file_name, code)

            # Execute the file after writing to see if it works
            try:
                result = run_code(code)
                return f"Code written to {file_name} and executed with result:\n{result}"
            except Exception as e:
                return f"Code written to {file_name} but execution failed: {str(e)}"
        else:
            # Just execute the code
            try:
                result = run_code(code)
                return f"Code executed with result:\n{result}"
            except Exception as e:
                return f"Code execution failed: {str(e)}"
