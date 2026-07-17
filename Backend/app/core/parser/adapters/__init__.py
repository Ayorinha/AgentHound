"""Adapter dispatch: framework -> IR builder."""

from __future__ import annotations

from typing import Any

from ...ir.models import AnalysisIR, IRValidationError, SourceFramework
from . import crewai_adapter, dify_adapter, generic_adapter, langgraph_adapter

_ADAPTERS = {
    SourceFramework.GENERIC: generic_adapter.load,
    SourceFramework.CREWAI: crewai_adapter.load,
    SourceFramework.DIFY: dify_adapter.load,
    SourceFramework.LANGGRAPH: langgraph_adapter.load,
}


def run_adapter(framework: SourceFramework, data: dict[str, Any], analysis_id: str) -> AnalysisIR:
    """Build the IR for the given framework, wrapping unimplemented adapters."""
    loader = _ADAPTERS.get(framework)
    if loader is None:
        raise IRValidationError("UNKNOWN_FRAMEWORK", f"No adapter for framework {framework}.")
    try:
        return loader(data, analysis_id)
    except NotImplementedError as exc:
        raise IRValidationError(
            "ADAPTER_NOT_IMPLEMENTED",
            str(exc),
            {"framework": framework.value},
        ) from exc
