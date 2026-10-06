import os
import sys
from pathlib import Path

# Set required environment variables for the config module
os.environ.setdefault("DOCUMENT_DIR", "data/documents")
os.environ.setdefault("LLM_BASE_URL", "http://localhost.test")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("CHUNK_SIZE", "500")
os.environ.setdefault("CHUNK_OVERLAP", "50")
os.environ.setdefault("TOP_K", "4")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))