# 🧠 My Local LLaMA Dev Agent

This project is a local developer assistant powered by LLaMA 3.3 (via Ollama) and vector memory (ChromaDB). It breaks down tasks, executes code, and remembers past work.

### 🔧 Setup

```bash
git clone https://github.com/your-username/MyAgents.git
cd MyAgents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Make sure Ollama is installed and the llama3 model is downloaded:

bash
Copy
Edit
ollama run llama3
🚀 Run from CLI
bash
Copy
Edit
python llama_dev_agent.py
💻 Run the Web UI
bash
Copy
Edit
streamlit run streamlit_ui.py
Everything is private and local to your machine.

🧠 Features
Task breakdown with LLaMA

Local memory via ChromaDB

Step-by-step execution

File writing + terminal execution

Streamlit UI + CLI
