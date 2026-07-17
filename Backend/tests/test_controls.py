"""Control recommendation and simulation (spec sections 11, 12.5-12.6, 16)."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.controls import recommender, simulator
from app.core.ir.models import ControlApplication
from app.core.pipeline import analyze_text
from app.main import app

from .conftest import fixture_text

client = TestClient(app)


def _create(name: str) -> str:
    """Parse then analyze, so findings exist for the control endpoints."""
    resp = client.post(
        "/analyses",
        files={"file": (name, fixture_text(name), "application/x-yaml")},
    )
    assert resp.status_code == 200, resp.text
    analysis_id = resp.json()["analysis_id"]
    analyzed = client.post(f"/analyses/{analysis_id}/analyze", json=None)
    assert analyzed.status_code == 200, analyzed.text
    return analysis_id


def _rule_ids(findings):
    return {f["rule_id"] for f in findings}


# --- recommender ---------------------------------------------------------


def test_recommendations_shape_and_ranking():
    analysis_id = _create("hiresmart_generic.yaml")
    body = client.get(f"/analyses/{analysis_id}/controls/recommendations").json()
    recs = body["recommendations"]
    assert recs
    expected = {
        "control_id",
        "name",
        "target_node_id",
        "breaks_findings",
        "estimated_risk_reduction",
        "cost_estimate",
        "demo_priority",
    }
    assert all(expected <= r.keys() for r in recs)
    # Ranked by estimated risk reduction, descending.
    reductions = [r["estimated_risk_reduction"] for r in recs]
    assert reductions == sorted(reductions, reverse=True)
    # humanInTheLoop on the external email is the headline recommendation and
    # actually breaks findings.
    hitl = next(
        r for r in recs if r["control_id"] == "humanInTheLoop" and r["target_node_id"] == "output_email_candidate"
    )
    assert hitl["breaks_findings"]
    assert hitl["estimated_risk_reduction"] > 0


def test_recommendations_unknown_analysis_404():
    resp = client.get("/analyses/nope/controls/recommendations")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"


# --- simulation: spec section 16 acceptance criteria ---------------------


def test_human_in_the_loop_breaks_exfiltration_path():
    """Spec section 16: applying humanInTheLoop on the external email breaks the
    FH-001 exfiltration path."""
    analysis_id = _create("hiresmart_generic.yaml")
    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={"controls_to_apply": [{"control_id": "humanInTheLoop", "target_node_id": "output_email_candidate"}]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["before"]["finding_count"] > body["after"]["finding_count"]
    assert body["risk_reduction"]["absolute"] > 0
    broken = {bp["rule_id"] for bp in body["broken_paths"]}
    assert "FH-001" in broken
    assert all(bp["broken_by"] == "humanInTheLoop" for bp in body["broken_paths"])

    # The send edge into the external email is flagged blocked in the graph.
    send_edge = next(e for e in body["graph"]["edges"] if e["id"] == "edge_006")
    assert send_edge["blocked"] is True
    # The applied control appears as a first-class node (spec section 11).
    assert any(n["type"] == "control" for n in body["graph"]["nodes"])


def test_content_validation_drops_fh006():
    """Spec section 16: applying contentValidation on the fetched external asset
    makes the FH-006 indirect-injection finding disappear."""
    analysis_id = _create("hiresmart_fetchweb.yaml")
    before = client.get(f"/analyses/{analysis_id}/findings").json()["findings"]
    assert "FH-006" in _rule_ids(before)

    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={"controls_to_apply": [{"control_id": "contentValidation", "target_node_id": "asset_external_web"}]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "FH-006" in {bp["rule_id"] for bp in body["broken_paths"]}
    fetch_edge = next(e for e in body["graph"]["edges"] if e["id"] == "edge_002")
    assert fetch_edge["blocked"] is True


def test_partial_control_marks_edge_mitigated():
    analysis_id = _create("hiresmart_generic.yaml")
    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={"controls_to_apply": [{"control_id": "leastPrivilege", "target_node_id": "asset_cv_attachments"}]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # leastPrivilege has partial effect, so the read edge into the CV asset is
    # mitigated rather than hard-blocked.
    read_edge = next(e for e in body["graph"]["edges"] if e["id"] == "edge_003")
    assert read_edge["mitigated"] is True
    assert read_edge["blocked"] is False


def test_block_dominates_mitigation_on_shared_edge():
    """When a total and a partial control both hit the same edge, the edge is
    blocked and not also mitigated, regardless of application order."""
    analysis_id = _create("hiresmart_generic.yaml")
    # Partial (outputFiltering) listed first, total (humanInTheLoop) second, so
    # the mitigation is recorded before the block discards it.
    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={
            "controls_to_apply": [
                {"control_id": "outputFiltering", "target_node_id": "output_email_candidate"},
                {"control_id": "humanInTheLoop", "target_node_id": "output_email_candidate"},
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    send_edge = next(e for e in resp.json()["graph"]["edges"] if e["id"] == "edge_006")
    assert send_edge["blocked"] is True
    assert send_edge["mitigated"] is False


def test_duplicate_applications_are_deduplicated():
    """Repeating the same (control_id, target_node_id) must not produce duplicate
    applied_controls or duplicate control node ids in the graph."""
    analysis_id = _create("hiresmart_generic.yaml")
    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={
            "controls_to_apply": [
                {"control_id": "humanInTheLoop", "target_node_id": "output_email_candidate"},
                {"control_id": "humanInTheLoop", "target_node_id": "output_email_candidate"},
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["applied_controls"]) == 1
    node_ids = [n["id"] for n in body["graph"]["nodes"]]
    assert len(node_ids) == len(set(node_ids))


def test_simulate_unknown_control_rejected():
    analysis_id = _create("hiresmart_generic.yaml")
    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={"controls_to_apply": [{"control_id": "notAControl", "target_node_id": "output_email_candidate"}]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "UNKNOWN_CONTROL"


def test_simulate_unknown_target_rejected():
    analysis_id = _create("hiresmart_generic.yaml")
    resp = client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={"controls_to_apply": [{"control_id": "humanInTheLoop", "target_node_id": "ghost_node"}]},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "UNKNOWN_TARGET_NODE"


def test_simulate_empty_selection_is_a_noop():
    analysis_id = _create("hiresmart_generic.yaml")
    resp = client.post(f"/analyses/{analysis_id}/simulate-controls", json={"controls_to_apply": []})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["before"] == body["after"]
    assert body["risk_reduction"]["absolute"] == 0.0
    assert body["broken_paths"] == []


def test_simulate_does_not_mutate_stored_analysis():
    analysis_id = _create("hiresmart_generic.yaml")
    before = client.get(f"/analyses/{analysis_id}/findings").json()["findings"]
    client.post(
        f"/analyses/{analysis_id}/simulate-controls",
        json={"controls_to_apply": [{"control_id": "humanInTheLoop", "target_node_id": "output_email_candidate"}]},
    )
    after = client.get(f"/analyses/{analysis_id}/findings").json()["findings"]
    assert before == after


# --- core layer directly -------------------------------------------------


def test_simulator_evaluate_matches_recommender_source():
    result = analyze_text(fixture_text("hiresmart_generic.yaml"))
    outcome = simulator.evaluate(
        result, [ControlApplication(control_id="humanInTheLoop", target_node_id="output_email_candidate")]
    )
    assert outcome["risk_reduction"]["absolute"] > 0
    recs = recommender.recommend(result)["recommendations"]
    assert any(r["control_id"] == "humanInTheLoop" for r in recs)


# --- ControlApplication.status enum validation (A4) -------------------------


def test_control_application_rejects_invalid_status():
    with pytest.raises(ValidationError):
        ControlApplication(control_id="humanInTheLoop", target_node_id="n1", status="bypass")


def test_control_application_accepts_valid_statuses():
    for status in ("absent", "partial", "present", "bypassed"):
        ca = ControlApplication(control_id="humanInTheLoop", target_node_id="n1", status=status)
        assert ca.status == status
