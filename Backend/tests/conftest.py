"""Shared test configuration.

Point the repository at a throwaway data directory before any app import so
tests never write into the real ``data/`` folder.
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile
from pathlib import Path

# Always override (not setdefault) so a developer's real AGENTHOUND_DATA_DIR is
# never written to during a test run, and clean the throwaway dir up at exit.
_TMP_DATA_DIR = tempfile.mkdtemp(prefix="ah_test_")
atexit.register(shutil.rmtree, _TMP_DATA_DIR, ignore_errors=True)
os.environ["AGENTHOUND_DATA_DIR"] = _TMP_DATA_DIR

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def rule_ids(findings) -> set[str]:
    """Set of rule ids present in a findings list (membership assertions)."""
    return {f.rule_id for f in findings}


def findings_for(findings, rule_id: str) -> list:
    """All findings emitted by a single rule (count / evidence assertions)."""
    return [f for f in findings if f.rule_id == rule_id]
