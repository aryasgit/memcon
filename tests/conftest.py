"""
Pytest configuration — runs the suite in FULL ISOLATION so it never touches the
real memory: a throwaway vault dir + a dedicated Qdrant collection. The env vars
MUST be set before any memcon module is imported (config/writer/qdrant_store read
them at import time), so they live at the top of this file.
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

_TMP_VAULT = tempfile.mkdtemp(prefix="memcon_pytest_vault_")
os.environ["MEMCON_VAULT"] = _TMP_VAULT
os.environ["MEMCON_COLLECTION"] = "memcon_pytest"
os.environ.setdefault("MEMCON_BG_WORKERS", "2")
os.environ.setdefault("MEMCON_WATCH_DEBOUNCE", "0.3")

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_env():
    """Drop the throwaway Qdrant collection + temp vault when the session ends."""
    yield
    try:
        from memory.qdrant_store import _get_client, COLLECTION
        _get_client().delete_collection(COLLECTION)
    except Exception:
        pass
    shutil.rmtree(_TMP_VAULT, ignore_errors=True)


@pytest.fixture
def vault() -> Path:
    return Path(_TMP_VAULT)
