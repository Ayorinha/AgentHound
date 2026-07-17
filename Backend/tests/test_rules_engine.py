"""Integration tests for the rules pipeline (``app/core/rules/engine.py``).

These drive the whole analyze → rules → findings pipeline over realistic
fixtures and assert cross-rule, engine-level behavior: that the expected rules
co-fire on a known architecture, that findings carry the acceptance-criteria
fields, and that they are ordered and identified deterministically.

Per-rule unit tests live in test_path_rules.py, test_node_rules.py and
test_edge_rules.py.
"""

from app.core.pipeline import analyze_text

from .conftest import fixture_text, rule_ids


def test_hiresmart_detects_full_exfiltration():
    result = analyze_text(fixture_text("hiresmart_generic.yaml"))
    ids = rule_ids(result.findings)
    assert "FH-001" in ids
    assert "FH-002" in ids

    fh1 = next(f for f in result.findings if f.rule_id == "FH-001")
    # Acceptance criteria (spec section 16): finding carries these fields.
    assert fh1.path and fh1.score > 0 and fh1.severity
    assert fh1.evidence and fh1.recommended_controls
    assert "humanInTheLoop" in fh1.recommended_controls
    assert fh1.severity.value == "critical"


def test_fetchweb_detects_indirect_injection():
    result = analyze_text(fixture_text("hiresmart_fetchweb.yaml"))
    assert "FH-006" in rule_ids(result.findings)


def test_findings_sorted_by_score_desc():
    result = analyze_text(fixture_text("hiresmart_generic.yaml"))
    scores = [f.score for f in result.findings]
    assert scores == sorted(scores, reverse=True)
    assert result.findings[0].id == "finding_001"


def test_safe_architecture_has_no_critical_path():
    # Same shape as the exfiltration fixture but the external output now requires
    # approval and the asset is public: no path rule should fire.
    safe = """
metadata: {name: Safe}
nodes:
  - {id: in1, type: input, name: Form, properties: {trust_level: untrusted}}
  - {id: ag1, type: agent, name: Agent}
  - {id: as1, type: data_asset, name: Docs, properties: {sensitivity: public, boundary: internal}}
  - {id: out1, type: output, name: Chat, properties: {boundary: internal, approval_gate_present: true}}
edges:
  - {id: e1, source: in1, target: ag1, capability: receiveInstruction}
  - {id: e2, source: ag1, target: as1, capability: read}
  - {id: e3, source: as1, target: out1, capability: send}
"""
    result = analyze_text(safe)
    assert "FH-001" not in rule_ids(result.findings)
    assert "FH-003" not in rule_ids(result.findings)
