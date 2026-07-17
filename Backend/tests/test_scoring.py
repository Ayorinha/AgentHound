import pytest

from app.core.ir.models import Severity
from app.core.rules.scoring import ScoreInputs, compute_score, severity_from_score


def test_score_clamped_to_ten():
    score = compute_score(
        ScoreInputs(
            base_severity="critical",
            data_sensitivity="critical",
            external_reach="external",
            controls_absent=["approval_missing", "validation_missing", "allowlist_missing"],
            reversible=False,
            agent_count=3,
        )
    )
    assert score == 10.0


def test_score_additive_components():
    # base high (6.0) + medium sensitivity (0.8) + internal (0) + no controls + reversible + 1 agent
    score = compute_score(ScoreInputs(base_severity="high", data_sensitivity="medium"))
    assert score == 6.8


def test_existing_controls_credit_reduces_score():
    base = compute_score(ScoreInputs(base_severity="high"))
    reduced = compute_score(ScoreInputs(base_severity="high", existing_controls_credit=2.0))
    assert reduced == base - 2.0


def test_unknown_base_severity_fails_fast():
    with pytest.raises(ValueError):
        compute_score(ScoreInputs(base_severity="bogus"))


def test_severity_thresholds():
    assert severity_from_score(9.0) == Severity.CRITICAL
    assert severity_from_score(7.0) == Severity.HIGH
    assert severity_from_score(4.0) == Severity.MEDIUM
    assert severity_from_score(2.0) == Severity.LOW
    assert severity_from_score(1.0) == Severity.INFO
