# memory.py

import os
from datetime import datetime
import chromadb
from langchain_community.embeddings import OllamaEmbeddings

MEMORY_LOG = "workspace/memory_log.md"


class Memory:
    def __init__(self):
        os.makedirs("workspace", exist_ok=True)

        # Initialize the embedder
        # Note: This will show a deprecation warning, but will still work for now
        self.embedder = OllamaEmbeddings(model="llama3")

        # Initialize the ChromaDB client
        self.client = chromadb.PersistentClient(path="workspace/chroma")

        # Try to get the collection if it exists, otherwise create it
        try:
            self.collection = self.client.get_collection(name="agent-memory")
            print("Found existing collection 'agent-memory'")
        except chromadb.errors.NotFoundError:
            # Collection doesn't exist, create it
            print("Creating new collection 'agent-memory'")
            self.collection = self.client.create_collection(name="agent-memory")

        self.memory = []

    def log_task(self, task):
        entry = f"### Task: {task}\nTime: {datetime.now()}\n"
        self._write(entry)
        self.memory.append({"task": task})
        self._embed_and_store(task, metadata={"type": "task"})

    def log_plan(self, plan):
        entry = "\n**Plan:**\n" + "\n".join(f"- {step}" for step in plan) + "\n"
        self._write(entry)
        self.memory[-1]["plan"] = plan
        self._embed_and_store(" ".join(plan), metadata={"type": "plan"})

    def log_result(self, step, result):
        entry = f"\n✅ Step: {step}\nResult:\n{result}\n"
        self._write(entry)
        self.memory[-1].setdefault("results", []).append({"step": step, "result": result})
        self._embed_and_store(result, metadata={"type": "result", "step": step})

    def search_memory(self, query, top_k=3):
        # Get embedding for query
        query_embedding = self.embedder.embed_query(query)

        # Convert to list for ChromaDB compatibility
        query_embedding_list = list(query_embedding)

        try:
            # Query collection with embedding
            results = self.collection.query(
                query_embeddings=[query_embedding_list],
                n_results=min(top_k, len(self.collection.get()['ids']))
            )
            matches = results.get("documents", [[]])[0]
        except Exception as e:
            print(f"Error during search: {e}")
            matches = []

        return matches

    def _embed_and_store(self, text, metadata):
        try:
            # Get embedding for the text
            embedding = self.embedder.embed_query(text)

            # Convert to list for ChromaDB compatibility
            embedding_list = list(embedding)

            # Create a unique ID
            collection_data = self.collection.get()
            next_id = str(len(collection_data['ids']) + 1)

            # Add to collection with embedding
            self.collection.add(
                documents=[text],
                embeddings=[embedding_list],
                ids=[next_id],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error storing in ChromaDB: {e}")

    def _write(self, text):
        with open(MEMORY_LOG, "a") as f:
            f.write(text + "\n")