"""Telco RAG package (flat src/ layout).

Imports inside the package use bare module names (``from domain import ...``,
``from rag.pipeline import ...``). To make those work both under pytest (which
adds ``src/`` to ``sys.path``) and via the installed ``telco-rag`` console
script, put this package's directory on ``sys.path`` on import.
"""

import sys
from pathlib import Path

_PKG_DIR = str(Path(__file__).resolve().parent)
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)
