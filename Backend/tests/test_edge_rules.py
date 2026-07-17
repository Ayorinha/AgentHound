"""Unit tests for the edge-relationship rules in ``app/core/rules/edge_rules.py``.

These rules reason over a single capability edge (delegation, data flow,
external read, retry). Each rule is exercised with a minimal generic-YAML
architecture so the trigger and its negative case are isolated.
"""

from app.core.pipeline import analyze_text

from .conftest import rule_ids


# --- FH-023: delegateTo edge where target agent has extra capabilities --------
# The rule suppresses when source_caps == target_caps.  To make them equal, ag2
# is given a delegateTo edge targeting a tool (skipped by fh_023 because the
# target is not an agent) so both agents end up with {delegateTo, executeCode}.

_FH023 = """
metadata: {{name: FH023}}
nodes:
  - {{id: ag1, type: agent, name: Planner}}
  - {{id: ag2, type: agent, name: Worker}}
  - {{id: t1, type: tool, name: exec.run}}{extra_nodes}
edges:
  - {{id: e1, source: ag1, target: ag2, capability: delegateTo}}
  - {{id: e2, source: ag2, target: t1, capability: executeCode}}{extra_edges}
"""


def test_fh023_fires_when_target_has_extra_capability():
    result = analyze_text(_FH023.format(extra_nodes="", extra_edges=""))
    assert "FH-023" in rule_ids(result.findings)


def test_fh023_suppressed_when_caps_equal():
    # Give ag1 the executeCode cap and ag2 the delegateTo cap so both sets are
    # identical: source_caps == target_caps => rule suppresses.
    extra_nodes = "\n  - {id: t2, type: tool, name: helper}"
    extra_edges = (
        "\n  - {id: e3, source: ag1, target: t1, capability: executeCode}"
        "\n  - {id: e4, source: ag2, target: t2, capability: delegateTo}"
    )
    result = analyze_text(_FH023.format(extra_nodes=extra_nodes, extra_edges=extra_edges))
    assert "FH-023" not in rule_ids(result.findings)


# --- FH-024: dataFlow between agents without any validation guardrail ---------

_FH024 = """
metadata: {{name: FH024}}
nodes:
  - {{id: ag1, type: agent, name: Source, properties: {{guardrails: {guardrails}}}}}
  - {{id: ag2, type: agent, name: Target}}
edges:
  - {{id: e1, source: ag1, target: ag2, capability: dataFlow}}
"""


def test_fh024_fires_without_validation_guardrail():
    result = analyze_text(_FH024.format(guardrails="[]"))
    assert "FH-024" in rule_ids(result.findings)


def test_fh024_suppressed_when_source_has_content_validation():
    result = analyze_text(_FH024.format(guardrails="[contentValidation]"))
    assert "FH-024" not in rule_ids(result.findings)


# --- FH-025: read from external data asset without content validation ---------

_FH025 = """
metadata: {{name: FH025}}
nodes:
  - {{id: ag1, type: agent, name: Agent, properties: {{guardrails: {guardrails}}}}}
  - {{id: da1, type: data_asset, name: ExtDB, properties: {{boundary: external}}}}
edges:
  - {{id: e1, source: ag1, target: da1, capability: read}}
"""


def test_fh025_fires_without_content_validation():
    result = analyze_text(_FH025.format(guardrails="[]"))
    assert "FH-025" in rule_ids(result.findings)


def test_fh025_suppressed_when_agent_has_content_validation():
    result = analyze_text(_FH025.format(guardrails="[contentValidation]"))
    assert "FH-025" not in rule_ids(result.findings)


# --- FH-031: retry capability on a non-idempotent tool -----------------------

_FH031 = """
metadata: {{name: FH031}}
nodes:
  - {{id: ag1, type: agent, name: Caller}}
  - {{id: t1, type: tool, name: payment.charge, properties: {{idempotent: {idempotent}}}}}
edges:
  - {{id: e1, source: ag1, target: t1, capability: retry}}
"""


def test_fh031_fires_on_non_idempotent_tool():
    result = analyze_text(_FH031.format(idempotent="false"))
    assert "FH-031" in rule_ids(result.findings)


def test_fh031_suppressed_when_tool_is_idempotent():
    result = analyze_text(_FH031.format(idempotent="true"))
    assert "FH-031" not in rule_ids(result.findings)
