

# 🧠 LocalGenius

**LocalGenius** is a local-first, privacy-preserving dev agent powered by [LLaMA 3](https://ollama.com/library/llama3) and [ChromaDB](https://www.trychroma.com/). It breaks down tasks, executes them, stores memory, and runs entirely on your machine — via CLI or Web UI.

---

## 🚀 Quickstart

### 1. Clone and bootstrap

```bash
git clone https://github.com/peanutlife/localgenius.git
cd localgenius
./bootstrap.sh
```

> This sets up the Python virtualenv, installs dependencies, and launches the LLaMA 3 model using Ollama.

---

## 💻 Run the Agent

### CLI mode

```bash
python llama_dev_agent.py
```

### Web UI (Streamlit)

```bash
streamlit run streamlit_ui.py
```

> Opens at: [http://localhost:8501](http://localhost:8501)

---

## 🧠 Features

- 🔍 Task breakdown using LLaMA 3
- 🧐 Memory recall via ChromaDB
- ⚖️ Step-by-step code generation and execution
- 📃 Writes files and executes scripts
- 💻 Dual interface: CLI + Streamlit
- 🔐 100% private and local

---

## 🛠 Requirements

- Python 3.9+
- [Ollama](https://ollama.com/download)
- Run `ollama run llama3` at least once to download the model

---

## 🤕 Example Task

Try this in CLI or UI:

```text
Create a script that fetches GitHub trending repos and writes them to JSON
```

---

## 💪 bootstrap.sh (optional setup script)

```bash
#!/bin/bash

echo "🧠 Bootstrapping LocalGenius setup..."
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

if command -v ollama &> /dev/null
then
  echo "🚀 Checking for llama3 model..."
  ollama run llama3 &
else
  echo "⚠️ Ollama not found. Please install it: https://ollama.com/download"
fi

echo "✅ Setup complete. Run with:"
echo "  python llama_dev_agent.py"
echo "  streamlit run streamlit_ui.py"
```

---

## 📊 Badges

![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4-red)
![Built with LLaMA 3](https://img.shields.io/badge/Model-LLaMA%203-blueviolet)
![Runs locally](https://img.shields.io/badge/Privacy-Local%20Only-green)

---

## 🙌 Credits

Built by [@peanutlife](https://github.com/peanutlife) with ❤️, ChatGPT, LLaMA, and local-first power.
```
