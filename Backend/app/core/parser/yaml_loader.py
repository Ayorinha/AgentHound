"""YAML loading and framework detection (spec section 5.2).

Loads YAML safely, rejects empty documents, and applies the simple heuristic
from the spec to pick an adapter when the caller does not specify one.
"""

from __future__ import annotations

from typing import Any

import yaml

from ..ir.models import IRValidationError, SourceFramework


def load_yaml_text(text: str) -> dict[str, Any]:
    """Parse YAML text into a mapping. Rejects empty or non-mapping documents."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # malformed YAML
        raise IRValidationError("INVALID_YAML", f"Could not parse YAML: {exc}") from exc

    if data is None or (isinstance(data, (dict, list, str)) and len(data) == 0):
        raise IRValidationError("EMPTY_INPUT", "The uploaded architecture is empty.")
    if not isinstance(data, dict):
        raise IRValidationError(
            "INVALID_INPUT", "Top-level YAML must be a mapping.", {"got": type(data).__name__}
        )
    return data


def detect_framework(data: dict[str, Any]) -> SourceFramework:
    """Heuristic framework detection (spec section 5.2).

    Refines the spec's sketch in one place: a real Dify DSL nests its nodes under
    ``workflow.graph``, not at the top level. The ``workflow.graph`` shape (which
    the generic/LangGraph inputs never use) is the reliable Dify signal, checked
    before the bare ``graph`` key that LangGraph shares. Requiring the ``graph``
    key -- rather than any stray top-level ``workflow`` -- keeps a non-Dify input
    from being mis-routed into the Dify adapter; a Dify DSL whose graph is merely
    malformed still lands there and gets the adapter's specific error.
    """
    if "agents" in data and "tasks" in data:
        return SourceFramework.CREWAI
    workflow = data.get("workflow")
    if isinstance(workflow, dict) and "graph" in workflow:
        return SourceFramework.DIFY
    if "state_graph" in data or "graph" in data:
        return SourceFramework.LANGGRAPH
    return SourceFramework.GENERIC
