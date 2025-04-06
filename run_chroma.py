# run_chroma.py

from chromadb.app import Chroma
from chromadb.config import Settings

server = Chroma(settings=Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./workspace/chroma"
))
server.run()
