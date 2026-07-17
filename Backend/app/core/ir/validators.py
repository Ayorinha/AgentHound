"""IR and finding validation (spec section 13).

All failures raise ``IRValidationError`` which carries the spec's error envelope
``{"error": {"code", "message", "details"}}``.
"""

from __future__ import annotations

from ..catalogs import capabilities as valid_capabilities
from .models import AnalysisIR, Finding, IRValidationError


def validate_ir(ir: AnalysisIR) -> None:
    """Validate a normalized IR. Raises IRValidationError on the first problem."""
    if not ir.nodes:
        raise IRValidationError("EMPTY_IR", "The architecture contains no nodes.")

    # Unique node ids.
    seen: set[str] = set()
    for node in ir.nodes:
        if node.id in seen:
            raise IRValidationError(
                "DUPLICATE_NODE_ID",
                f"Node id {node.id!r} is defined more than once.",
                {"node_id": node.id},
            )
        seen.add(node.id)

    known_caps = valid_capabilities()
    node_ids = seen
    edge_ids: set[str] = set()
    for edge in ir.edges:
        if edge.id in edge_ids:
            raise IRValidationError(
                "DUPLICATE_EDGE_ID",
                f"Edge id {edge.id!r} is defined more than once.",
                {"edge_id": edge.id},
            )
        edge_ids.add(edge.id)
        if edge.source not in node_ids:
            raise IRValidationError(
                "INVALID_IR",
                f"Edge {edge.id} references unknown node {edge.source}",
                {"edge_id": edge.id, "missing_node": edge.source},
            )
        if edge.target not in node_ids:
            raise IRValidationError(
                "INVALID_IR",
                f"Edge {edge.id} references unknown node {edge.target}",
                {"edge_id": edge.id, "missing_node": edge.target},
            )
        if edge.capability not in known_caps:
            raise IRValidationError(
                "UNKNOWN_CAPABILITY",
                f"Edge {edge.id} uses capability {edge.capability!r} which is not in the catalog.",
                {"edge_id": edge.id, "capability": edge.capability},
            )


def validate_findings(findings: list[Finding]) -> None:
    """Ensure each finding carries the mandatory fields (spec section 13).

    The Finding model already guarantees ``severity`` (enum) and ``score``
    (float in [0, 10]) by construction, so this checks the parts the model
    cannot: a non-empty ``rule_id`` and a non-empty ``path``. ``edges``,
    ``evidence`` and ``recommended_controls`` are intentionally NOT required to
    be non-empty -- the spec mandates only that they be present, and future
    node-only findings may legitimately omit them.
    """
    for finding in findings:
        if not finding.rule_id:
            raise IRValidationError("INVALID_FINDING", "Finding is missing rule_id.", {"finding_id": finding.id})
        if not finding.path:
            raise IRValidationError(
                "INVALID_FINDING",
                f"Finding {finding.id} has an empty path.",
                {"finding_id": finding.id, "rule_id": finding.rule_id},
            )
