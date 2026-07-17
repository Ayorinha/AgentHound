"""End-to-end tests for the Phase 3 framework adapters (spec section 5).

Each framework has a risky fixture (which must surface specific findings) and a
safe fixture (which must surface none), all driven through the full pipeline via
``analyze_text`` with automatic framework detection.
"""

import pytest

from app.core.ir.models import SourceFramework
from app.core.parser.yaml_loader import detect_framework, load_yaml_text
from app.core.pipeline import analyze_text
from app.core.rules.common import HYGIENE_RULE_IDS

from .conftest import fixture_text


def _rule_ids(findings):
    return {f.rule_id for f in findings}


def _attack_findings(findings):
    """Return findings whose finding_class is 'attack' (not hygiene/compliance)."""
    return [f for f in findings if f.finding_class == "attack"]


@pytest.mark.parametrize(
    "fixture,expected",
    [
        ("crewai_risky.yaml", SourceFramework.CREWAI),
        ("crewai_safe.yaml", SourceFramework.CREWAI),
        ("dify_risky.yaml", SourceFramework.DIFY),
        ("dify_safe.yaml", SourceFramework.DIFY),
        ("langgraph_risky.yaml", SourceFramework.LANGGRAPH),
        ("langgraph_safe.yaml", SourceFramework.LANGGRAPH),
    ],
)
def test_framework_detection(fixture, expected):
    assert detect_framework(load_yaml_text(fixture_text(fixture))) is expected


def test_stray_workflow_key_is_not_misrouted_to_dify():
    # A top-level `workflow` without the Dify `graph` shape must fall through to
    # the intended adapter (generic here), not be forced into the Dify adapter.
    data = load_yaml_text(
        "workflow: {name: my flow}\nnodes:\n  - {id: n1, type: agent, name: N}\n"
    )
    assert detect_framework(data) is SourceFramework.GENERIC


# --- finding_class channel separation ---------------------------------------


def test_finding_class_attack_channel_empty_for_safe_fixture():
    # The attack channel of a safe fixture must be empty; the hygiene channel
    # may still surface compliance gaps (that is the point of the separation).
    result = analyze_text(fixture_text("crewai_safe.yaml"))
    attack = [f for f in result.findings if f.finding_class == "attack"]
    hygiene = [f for f in result.findings if f.finding_class == "hygiene"]
    assert attack == []
    assert all(f.rule_id in HYGIENE_RULE_IDS for f in hygiene)


def test_finding_class_serialized_in_model_dump():
    result = analyze_text(fixture_text("crewai_risky.yaml"))
    for finding in result.findings:
        d = finding.model_dump()
        assert d["finding_class"] in {"attack", "hygiene"}


# --- CrewAI -----------------------------------------------------------------


def test_crewai_risky_surfaces_expected_findings():
    result = analyze_text(fixture_text("crewai_risky.yaml"))
    assert result.ir.source_framework is SourceFramework.CREWAI
    ids = _rule_ids(result.findings)
    assert {"FH-002", "FH-003", "FH-014"} <= ids


def test_crewai_safe_is_clean():
    result = analyze_text(fixture_text("crewai_safe.yaml"))
    assert _attack_findings(result.findings) == []


# --- Dify -------------------------------------------------------------------


def test_dify_risky_surfaces_read_and_external_send():
    result = analyze_text(fixture_text("dify_risky.yaml"))
    assert result.ir.source_framework is SourceFramework.DIFY
    ids = _rule_ids(result.findings)
    assert {"FH-002", "FH-003"} <= ids


def test_dify_safe_is_clean():
    result = analyze_text(fixture_text("dify_safe.yaml"))
    assert _attack_findings(result.findings) == []


def test_dify_agent_to_agent_edge_is_dataflow_not_delegation():
    # A Dify LLM -> LLM transition is ordinary data flow, not authority
    # delegation, so it must not be labelled delegateTo (which could trip FH-014).
    dsl = """
app: {name: TwoAgents, mode: workflow}
workflow:
  graph:
    nodes:
      - {id: start, data: {type: start, title: In}}
      - {id: a, data: {type: llm, title: Planner}}
      - {id: b, data: {type: llm, title: Worker}}
      - {id: answer, data: {type: answer, title: Out}}
    edges:
      - {source: start, target: a, data: {}}
      - {source: a, target: b, data: {}}
      - {source: b, target: answer, data: {}}
"""
    result = analyze_text(dsl, framework_hint="dify")
    caps = {e.capability for e in result.ir.edges if e.source.startswith("agent_") and e.target.startswith("agent_")}
    assert caps == {"dataFlow"}
    assert "delegateTo" not in {e.capability for e in result.ir.edges}
    assert "FH-014" not in _rule_ids(result.findings)


# --- LangGraph --------------------------------------------------------------


def test_langgraph_risky_surfaces_exec_delegation_and_destruction():
    result = analyze_text(fixture_text("langgraph_risky.yaml"))
    assert result.ir.source_framework is SourceFramework.LANGGRAPH
    ids = _rule_ids(result.findings)
    assert {"FH-010", "FH-011", "FH-014"} <= ids


def test_langgraph_safe_is_clean():
    result = analyze_text(fixture_text("langgraph_safe.yaml"))
    assert _attack_findings(result.findings) == []


def test_output_derived_fields_consistent_for_mixed_case_boundary():
    # A declared "EXTERNAL" boundary must yield an external output_kind, not a
    # stale chat_response, even though the normalizer only canonicalises boundary.
    dsl = """
name: MixedCaseBoundary
state_graph:
  entry_point: agent
  nodes:
    - {name: user, type: input}
    - {name: agent, type: agent}
    - {name: sink, type: output, boundary: EXTERNAL}
  edges:
    - {source: user, target: agent}
    - {source: agent, target: sink}
"""
    result = analyze_text(dsl, framework_hint="langgraph")
    sink = next(n for n in result.ir.nodes if n.id == "output_sink")
    assert sink.properties["boundary"] == "external"
    assert sink.properties["output_kind"] == "external_action"


# --- adapter shape sanity ---------------------------------------------------


def test_crewai_single_file_shape_with_agents_and_tasks():
    result = analyze_text(fixture_text("crewai_risky.yaml"))
    types = {n.type.value for n in result.ir.nodes}
    assert {"agent", "input", "tool", "data_asset"} <= types


_CREWAI_DELEGATION = """
agents:
  intake:
    role: Intake
    trust_level: untrusted
    delegates_to: [privileged]
    has_scoped_delegation: {scoped}
  privileged:
    role: Privileged
    trust_level: trusted_core
tasks: {{}}
"""


def test_crewai_quoted_scoped_flag_does_not_suppress_fh014():
    # A quoted "false" must be coerced at ingestion; otherwise it becomes a truthy
    # string, marks the delegation scoped, and silently suppresses FH-014.
    result = analyze_text(_CREWAI_DELEGATION.format(scoped='"false"'), framework_hint="crewai")
    assert "FH-014" in _rule_ids(result.findings)


def test_crewai_genuinely_scoped_delegation_suppresses_fh014():
    result = analyze_text(_CREWAI_DELEGATION.format(scoped="true"), framework_hint="crewai")
    assert "FH-014" not in _rule_ids(result.findings)


def test_crewai_mixed_case_control_kind_gates_output():
    # A human-approval control declared with non-canonical casing must still be
    # recognised and gate the output, suppressing FH-003.
    yaml_text = """
agents:
  support:
    role: Support
    inputs:
      - {name: Inbound email, trust_level: untrusted}
    tools:
      - name: gmail.send
    controls:
      - {name: Approval, control_kind: Human_Approval, scope: [gmail.send]}
tasks: {}
"""
    result = analyze_text(yaml_text, framework_hint="crewai")
    assert "FH-003" not in _rule_ids(result.findings)


def test_empty_crewai_agents_rejected():
    from app.core.ir.models import IRValidationError

    with pytest.raises(IRValidationError):
        analyze_text("agents: {}\ntasks: {}\n", framework_hint="crewai")
