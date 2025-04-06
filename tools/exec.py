# tools/exec.py

import subprocess
import tempfile

def run_code(code):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
        temp.write(code)
        temp.flush()
        try:
            result = subprocess.run(["python3", temp.name], capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            return "Execution timed out."
