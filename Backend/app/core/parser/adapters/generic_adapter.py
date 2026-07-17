"""Generic YAML adapter (Phase 1).

The generic format is a thin, explicit authoring layer over the IR: the caller
declares ``nodes`` (each with ``type`` and ``properties``) and ``edges`` (each
with a neutral ``capability``). Missing edge ids are generated; missing node
properties are filled later by the normalizer.

This was the only adapter in Phase 1; the framework-specific adapters
(CrewAI/Dify/LangGraph) landed in Phase 3 and produce the same IR shape from their
native formats. The generic format remains the explicit authoring path.
"""

from __future__ import annotations

from typing import Any

from ...ir.models import (
    AnalysisIR,
    Edge,
    IRValidationError,
    Metadata,
    Node,
    NodeType,
    SourceFramework,
)

VALID_TYPES = {t.value for t in NodeType}


def _as_mapping(value: Any, field: str) -> dict[str, Any]:
    """Return value as a dict, or raise a structured error if it is not a mapping.

    Guards against malformed uploads (e.g. ``properties`` given as a list) that
    would otherwise raise a raw TypeError/AttributeError and surface as a 500.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IRValidationError(
            "INVALID_INPUT",
            f"{field} must be a mapping.",
            {"field": field, "got": type(value).__name__},
        )
    return dict(value)


def _coerce_node(raw: dict[str, Any], index: int) -> Node:
    if not isinstance(raw, dict):
        raise IRValidationError("INVALID_INPUT", f"nodes[{index}] must be a mapping.")
    node_id = raw.get("id")
    if not node_id:
        raise IRValidationError("INVALID_INPUT", f"nodes[{index}] is missing an id.")
    node_type = raw.get("type")
    if node_type not in VALID_TYPES:
        raise IRValidationError(
            "INVALID_NODE_TYPE",
            f"Node {node_id} has invalid type {node_type!r}.",
            {"node_id": node_id, "type": node_type, "valid": sorted(VALID_TYPES)},
        )
    return Node(
        id=str(node_id),
        type=NodeType(node_type),
        name=str(raw.get("name") or node_id),
        properties=_as_mapping(raw.get("properties"), f"nodes[{index}].properties"),
    )


def _coerce_edge(raw: dict[str, Any], index: int) -> Edge:
    if not isinstance(raw, dict):
        raise IRValidationError("INVALID_INPUT", f"edges[{index}] must be a mapping.")
    source = raw.get("source")
    target = raw.get("target")
    capability = raw.get("capability")
    if not source or not target or not capability:
        raise IRValidationError(
            "INVALID_INPUT",
            f"edges[{index}] requires source, target and capability.",
            {"edge": raw},
        )
    edge_id = raw.get("id") or f"edge_{index + 1:03d}"
    return Edge(
        id=str(edge_id),
        source=str(source),
        target=str(target),
        capability=str(capability),
        properties=_as_mapping(raw.get("properties"), f"edges[{index}].properties"),
    )


def load(data: dict[str, Any], analysis_id: str) -> AnalysisIR:
    """Build an (un-normalized) IR from generic declarative YAML."""
    # Distinguish "no nodes declared" (EMPTY_IR) from "nodes given with the wrong
    # type" (INVALID_INPUT), mirroring the edges/controls handling below: only a
    # missing key or an empty list is EMPTY_IR, while a present-but-non-list value
    # such as ``nodes: {}`` is a type error.
    raw_nodes = data.get("nodes")
    if raw_nodes is None:
        raise IRValidationError("EMPTY_IR", "Generic input declares no nodes.")
    if not isinstance(raw_nodes, list):
        raise IRValidationError("INVALID_INPUT", "'nodes' must be a list.", {"got": type(raw_nodes).__name__})
    if not raw_nodes:
        raise IRValidationError("EMPTY_IR", "Generic input declares no nodes.")

    # Only a missing key defaults to empty; a present-but-non-list value (even a
    # falsy one like {}) is rejected rather than silently coerced to [].
    raw_edges = data.get("edges")
    if raw_edges is None:
        raw_edges = []
    if not isinstance(raw_edges, list):
        raise IRValidationError("INVALID_INPUT", "'edges' must be a list.", {"got": type(raw_edges).__name__})

    nodes = [_coerce_node(raw, i) for i, raw in enumerate(raw_nodes)]
    edges = [_coerce_edge(raw, i) for i, raw in enumerate(raw_edges)]

    meta_raw = _as_mapping(data.get("metadata"), "metadata")
    metadata = Metadata(name=str(meta_raw.get("name") or "Generic architecture"))

    raw_controls = data.get("controls")
    if raw_controls is None:
        raw_controls = []
    if not isinstance(raw_controls, list):
        raise IRValidationError(
            "INVALID_INPUT", "'controls' must be a list.", {"got": type(raw_controls).__name__}
        )
    controls = [_as_mapping(c, f"controls[{i}]") for i, c in enumerate(raw_controls)]

    return AnalysisIR(
        analysis_id=analysis_id,
        source_framework=SourceFramework.GENERIC,
        metadata=metadata,
        nodes=nodes,
        edges=edges,
        controls=controls,
    )
