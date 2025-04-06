from chromadb.config import Settings
import chromadb

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./workspace/chroma"
))
print("🎉 IT WORKS!")

