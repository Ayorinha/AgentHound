"""Risk scoring (spec section 10).

Additive formula:

    score = base_severity_value
          + data_sensitivity_weight
          + external_reach_weight
          + control_absence_weight
          + reversibility_penalty
          + agent_count_weight
          - existing_controls_credit

clamped to [0, 10], then mapped to a final severity band.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..ir.models import Severity

BASE: dict[str, float] = {
    "critical": 8.0,
    "high": 6.0,
    "medium": 4.0,
    "low": 2.0,
    "info": 0.0,
}

DATA_SENSITIVITY_WEIGHT: dict[str, float] = {
    "public": 0.0,
    "low": 0.3,
    "medium": 0.8,
    "high": 1.8,
    "critical": 2.5,
}

EXTERNAL_REACH_WEIGHT: dict[str, float] = {
    "internal": 0.0,
    "perimeter": 1.0,
    "external": 2.0,
}

CONTROL_ABSENCE_WEIGHT: dict[str, float] = {
    "approval_missing": 1.0,
    "validation_missing": 0.8,
    "allowlist_missing": 0.7,
}

REVERSIBILITY_PENALTY = {True: 0.0, False: 1.0}  # keyed by "reversible?" boolean


@dataclass
class ScoreInputs:
    base_severity: str = "medium"
    data_sensitivity: str = "medium"
    external_reach: str = "internal"
    controls_absent: list[str] = field(default_factory=list)
    reversible: bool = True
    agent_count: int = 1
    existing_controls_credit: float = 0.0


def _agent_count_weight(agent_count: int) -> float:
    if agent_count <= 1:
        return 0.0
    if agent_count == 2:
        return 0.3
    return 0.8


def compute_score(inputs: ScoreInputs) -> float:
    # Fail fast on unknown enum keys rather than silently defaulting: a bad
    # base_severity/data_sensitivity/external_reach means a rule bug or typo,
    # and silently under-scoring a risk finding is the dangerous direction.
    try:
        score = BASE[inputs.base_severity]
        score += DATA_SENSITIVITY_WEIGHT[inputs.data_sensitivity]
        score += EXTERNAL_REACH_WEIGHT[inputs.external_reach]
    except KeyError as exc:
        raise ValueError(f"Unknown scoring input: {exc.args[0]!r}") from exc
    # A control code that is not weighted simply contributes nothing.
    score += sum(CONTROL_ABSENCE_WEIGHT.get(code, 0.0) for code in inputs.controls_absent)
    score += REVERSIBILITY_PENALTY[bool(inputs.reversible)]
    score += _agent_count_weight(inputs.agent_count)
    score -= inputs.existing_controls_credit
    return round(min(10.0, max(0.0, score)), 1)


def severity_from_score(score: float) -> Severity:
    if score >= 9.0:
        return Severity.CRITICAL
    if score >= 7.0:
        return Severity.HIGH
    if score >= 4.0:
        return Severity.MEDIUM
    if score >= 2.0:
        return Severity.LOW
    return Severity.INFO
