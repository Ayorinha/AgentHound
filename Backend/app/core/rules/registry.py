"""Access to the declarative rule catalog (spec sections 7-8).

Wraps ``core.catalogs.rule_catalog`` and provides a helper to assemble a
``Finding`` from a rule descriptor plus the runtime-derived score, path and
evidence.
"""

from __future__ import annotations

from typing import Any

from ..catalogs import rule_catalog
from ..ir.models import Finding, IRValidationError, Severity


def get_rule(rule_id: str) -> dict[str, Any]:
    rule = rule_catalog().get(rule_id)
    if rule is None:
        raise IRValidationError(
            "UNKNOWN_RULE",
            f"Rule {rule_id} is not defined in rules.yaml.",
            {"rule_id": rule_id},
        )
    return rule


def make_finding(
    *,
    rule_id: str,
    finding_id: str,
    severity: Severity,
    score: float,
    path: list[str],
    edges: list[str],
    evidence: dict[str, Any],
) -> Finding:
    """Build a Finding by combining catalog metadata with runtime data."""
    rule = get_rule(rule_id)
    return Finding(
        id=finding_id,
        rule_id=rule_id,
        title=rule.get("title", rule_id),
        severity=severity,
        score=score,
        category=rule.get("category", "capability_path"),
        path=path,
        edges=edges,
        derivation=rule.get("derivation", "").strip(),
        evidence=evidence,
        recommended_controls=list(rule.get("recommended_controls", [])),
        owasp_agentic=list(rule.get("owasp_agentic", [])),
        owasp_llm=list(rule.get("owasp_llm", [])),
        mitre_atlas=list(rule.get("mitre_atlas", [])),
    )
