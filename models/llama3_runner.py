# models/llama3_runner.py

import subprocess
import json

class LlamaRunner:
    def __init__(self, model_name="llama3"):
        self.model = model_name

    def run(self, prompt):
        command = ["ollama", "run", self.model]
        try:
            proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(prompt)
            if stderr:
                print(f"[LLaMA Error] {stderr}")
            return stdout.strip()
        except Exception as e:
            return f"[Runner Error] {str(e)}"
