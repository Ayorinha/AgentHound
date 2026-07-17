"""Control recommender (spec sections 11 and 12.5).

For every finding, each recommended control from the rule catalog is mapped to a
concrete target node -- the node the broken capability flows into on that
finding's path. Each distinct (control, target) candidate is then evaluated with
a single-control what-if simulation so its ``estimated_risk_reduction`` and the
findings it breaks are measured rather than guessed.
"""

from __future__ import annotations

from ..catalogs import control_catalog
from ..graph.traversal import DEFAULT_MAX_DEPTH
from ..ir.models import AnalysisResult, ControlApplication
from . import simulator

# Order in which demo priorities surface when risk reduction ties.
_PRIORITY_RANK = {"must_show": 0, "should_show": 1, "nice_to_have": 2}


def _candidate_target(finding, control_breaks: set[str], edge_map: dict) -> str | None:
    """The node the control should sit on for this finding: the target of the
    first edge on the finding's path whose capability the control breaks."""
    for edge_id in finding.edges:
        edge = edge_map.get(edge_id)
        if edge is not None and edge.capability in control_breaks:
            return edge.target
    return None


def recommend(result: AnalysisResult, *, max_depth: int = DEFAULT_MAX_DEPTH) -> dict:
    catalog = control_catalog()
    edge_map = result.ir.edge_map()

    # (control_id, target_node_id) -> ids of the findings that suggested it.
    candidates: dict[tuple[str, str], set[str]] = {}
    for finding in result.findings:
        for control_id in finding.recommended_controls:
            control = catalog.get(control_id)
            if control is None:
                continue  # a recommended control with no catalog entry is skipped
            breaks = set(control.get("breaks_capability_kinds", []))
            target = _candidate_target(finding, breaks, edge_map)
            if target is None:
                continue  # control does not apply to any hop on this path
            candidates.setdefault((control_id, target), set()).add(finding.id)

    recommendations: list[dict] = []
    for (control_id, target), _suggested_by in candidates.items():
        control = catalog[control_id]
        outcome = simulator.evaluate(
            result,
            [ControlApplication(control_id=control_id, target_node_id=target)],
            max_depth=max_depth,
        )
        recommendations.append(
            {
                "control_id": control_id,
                "name": control.get("name", control_id),
                "target_node_id": target,
                "breaks_findings": [bp["finding_id"] for bp in outcome["broken_paths"]],
                "estimated_risk_reduction": outcome["risk_reduction"]["absolute"],
                "cost_estimate": control.get("cost", "unknown"),
                "demo_priority": control.get("demo_priority", "nice_to_have"),
            }
        )

    recommendations.sort(
        key=lambda r: (
            -r["estimated_risk_reduction"],
            _PRIORITY_RANK.get(r["demo_priority"], 3),
            r["control_id"],
            r["target_node_id"],
        )
    )
    return {"recommendations": recommendations}
