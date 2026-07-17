"""Unit tests for the node-local property rules in ``app/core/rules/node_rules.py``.

These rules fire on a single node's properties (an input's trust level, an
output's boundary, a tool's audit flag, an agent's autonomy, a memory's TTL),
optionally checking for a mitigating control node. Each rule is exercised with a
minimal generic-YAML architecture so the trigger and its negative case are
isolated.
"""

from app.core.pipeline import analyze_text

from .conftest import rule_ids


# --- FH-021: untrusted input without sanitization ----------------------------

_FH021 = """
metadata: {{name: FH021}}
nodes:
  - {{id: in1, type: input, name: UserMsg, properties: {{trust_level: untrusted, sanitized_before_agent: {sanitized}}}}}
  - {{id: ag1, type: agent, name: Processor}}
edges:
  - {{id: e1, source: in1, target: ag1, capability: receiveInstruction}}
"""


def test_fh021_fires_without_sanitization():
    result = analyze_text(_FH021.format(sanitized="false"))
    assert "FH-021" in rule_ids(result.findings)


def test_fh021_suppressed_when_input_is_sanitized():
    result = analyze_text(_FH021.format(sanitized="true"))
    assert "FH-021" not in rule_ids(result.findings)


# --- FH-022: external output without content filter or PII redaction ---------

_FH022 = """
metadata: {{name: FH022}}
nodes:
  - {{id: out1, type: output, name: Response, properties: {{boundary: external, content_filter_present: {cf}}}}}
"""


def test_fh022_fires_without_content_filter():
    result = analyze_text(_FH022.format(cf="false"))
    assert "FH-022" in rule_ids(result.findings)


def test_fh022_suppressed_with_content_filter_present():
    result = analyze_text(_FH022.format(cf="true"))
    assert "FH-022" not in rule_ids(result.findings)


# --- FH-026: GDPR-regulated data asset without consent enforcement -----------

_FH026 = """
metadata: {{name: FH026}}
nodes:
  - {{id: da1, type: data_asset, name: UserPII, properties: {{contains_regulated_data: {regulated}}}}}
"""


def test_fh026_fires_on_gdpr_regulated_data():
    result = analyze_text(_FH026.format(regulated="[gdpr]"))
    assert "FH-026" in rule_ids(result.findings)


def test_fh026_suppressed_when_not_gdpr():
    result = analyze_text(_FH026.format(regulated="[other]"))
    assert "FH-026" not in rule_ids(result.findings)


# --- FH-027: side-effect tool with audit logging disabled --------------------

_FH027 = """
metadata: {{name: FH027}}
nodes:
  - {{id: t1, type: tool, name: db.write, properties: {{side_effect: true, audit_logging_enabled: {audit}}}}}
"""


def test_fh027_fires_when_audit_logging_disabled():
    result = analyze_text(_FH027.format(audit="false"))
    assert "FH-027" in rule_ids(result.findings)


def test_fh027_suppressed_when_audit_logging_enabled():
    result = analyze_text(_FH027.format(audit="true"))
    assert "FH-027" not in rule_ids(result.findings)


# --- FH-028: full-auto agent without a decision-audit-trail control ----------

_FH028 = """
metadata: {{name: FH028}}
nodes:
  - {{id: ag1, type: agent, name: AutoAgent, properties: {{autonomy_level: full_auto}}}}{control_node}
"""


def test_fh028_fires_without_decision_audit_trail():
    result = analyze_text(_FH028.format(control_node=""))
    assert "FH-028" in rule_ids(result.findings)


def test_fh028_suppressed_with_decision_audit_trail_control():
    ctrl = (
        "\n  - {id: c1, type: control, name: AuditCtrl,"
        " properties: {control_kind: decisionAuditTrail, target_node_id: ag1, status: present}}"
    )
    result = analyze_text(_FH028.format(control_node=ctrl))
    assert "FH-028" not in rule_ids(result.findings)


# --- FH-029: sensitive memory node without a retention TTL -------------------

_FH029 = """
metadata: {{name: FH029}}
nodes:
  - {{id: m1, type: memory, name: SensitiveStore, properties: {{sensitivity: high, retention_ttl_days: {ttl}}}}}
"""


def test_fh029_fires_when_ttl_absent():
    result = analyze_text(_FH029.format(ttl="~"))
    assert "FH-029" in rule_ids(result.findings)


def test_fh029_suppressed_when_ttl_set():
    result = analyze_text(_FH029.format(ttl="30"))
    assert "FH-029" not in rule_ids(result.findings)


# --- FH-032: irreversible deploy tool without rollback control ----------------

_FH032 = """
metadata: {{name: FH032}}
nodes:
  - {{id: ag1, type: agent, name: Deployer}}
  - {{id: t1, type: tool, name: deploy.tool, properties: {{side_effect_reversible: {reversible}}}}}
edges:
  - {{id: e1, source: ag1, target: t1, capability: deployRelease}}
"""


def test_fh032_fires_when_deploy_tool_is_irreversible():
    result = analyze_text(_FH032.format(reversible="false"))
    assert "FH-032" in rule_ids(result.findings)


def test_fh032_suppressed_when_deploy_tool_is_reversible():
    result = analyze_text(_FH032.format(reversible="true"))
    assert "FH-032" not in rule_ids(result.findings)


# --- FH-033: interpretIntent on untrusted input, direction-tolerant ----------

_FH033_INBOUND_INTERPRET = """
metadata: {name: FH033InboundInterpret}
nodes:
  - {id: in1, type: input, name: Prompt,
     properties: {trust_level: untrusted, injection_detector_present: false}}
  - {id: ag1, type: agent, name: Planner,
     properties: {autonomy_level: semi_auto_with_hitl}}
edges:
  - {id: e1, source: in1, target: ag1, capability: receiveInstruction}
  - {id: e2, source: in1, target: ag1, capability: interpretIntent}
"""


def test_fh033_fires_when_interpret_intent_is_inbound():
    """FH-033 must fire even when interpretIntent arrives *at* the agent (inbound edge)."""
    result = analyze_text(_FH033_INBOUND_INTERPRET)
    assert "FH-033" in rule_ids(result.findings)


# --- FH-034: external output with sensitive upstream read and no DLP control -

_FH034 = """
metadata: {{name: FH034}}
nodes:
  - {{id: ag1, type: agent, name: Agent}}
  - {{id: da1, type: data_asset, name: PII, properties: {{sensitivity: high}}}}
  - {{id: out1, type: output, name: ExtResponse, properties: {{boundary: external}}}}{control_node}
edges:
  - {{id: e1, source: ag1, target: da1, capability: read}}
  - {{id: e2, source: ag1, target: out1, capability: send}}
"""


def test_fh034_fires_without_dlp_control():
    result = analyze_text(_FH034.format(control_node=""))
    assert "FH-034" in rule_ids(result.findings)


def test_fh034_suppressed_with_dlp_control():
    ctrl = (
        "\n  - {id: c1, type: control, name: DLPCtrl,"
        " properties: {control_kind: dlpScanner, target_node_id: out1, status: present}}"
    )
    result = analyze_text(_FH034.format(control_node=ctrl))
    assert "FH-034" not in rule_ids(result.findings)


# --- FH-035: full-auto agent without anomaly-detection control ---------------

_FH035 = """
metadata: {{name: FH035}}
nodes:
  - {{id: ag1, type: agent, name: AutoAgent, properties: {{autonomy_level: full_auto}}}}{control_node}
"""


def test_fh035_fires_without_anomaly_detection():
    result = analyze_text(_FH035.format(control_node=""))
    assert "FH-035" in rule_ids(result.findings)


def test_fh035_suppressed_with_anomaly_detection_control():
    ctrl = (
        "\n  - {id: c1, type: control, name: AnomalyCtrl,"
        " properties: {control_kind: anomalyDetection, target_node_id: ag1, status: present}}"
    )
    result = analyze_text(_FH035.format(control_node=ctrl))
    assert "FH-035" not in rule_ids(result.findings)


# --- FH-004: one agent reads high/critical data AND sends to an external output

_FH004 = """
metadata: {{name: FH004OverPermissioned}}
nodes:
  - {{id: ag1, type: agent, name: Assistant}}
  - {{id: da1, type: data_asset, name: Secrets, properties: {{sensitivity: {sensitivity}}}}}
  - {{id: out1, type: output, name: Email, properties: {{boundary: external}}}}
edges:
  - {{id: e1, source: ag1, target: da1, capability: read}}
  - {{id: e2, source: ag1, target: out1, capability: send}}
"""


def test_fh004_fires_when_agent_reads_sensitive_and_sends_external():
    result = analyze_text(_FH004.format(sensitivity="high"))
    assert "FH-004" in rule_ids(result.findings)


def test_fh004_silent_when_read_asset_below_high_sensitivity():
    result = analyze_text(_FH004.format(sensitivity="medium"))
    assert "FH-004" not in rule_ids(result.findings)


# --- FH-005: side-effect tool with no approval that is irreversible -----------

_FH005 = """
metadata: {{name: FH005UnsafeTool}}
nodes:
  - {{id: t1, type: tool, name: db.drop,
     properties: {{side_effect: true, requires_approval: {approval}, side_effect_reversible: {reversible}}}}}
"""


def test_fh005_fires_on_unapproved_irreversible_side_effect():
    result = analyze_text(_FH005.format(approval="false", reversible="false"))
    assert "FH-005" in rule_ids(result.findings)


def test_fh005_silent_when_side_effect_is_reversible():
    result = analyze_text(_FH005.format(approval="false", reversible="true"))
    assert "FH-005" not in rule_ids(result.findings)


# --- FH-008: fetchWeb tool without a URL allowlist ---------------------------

_FH008 = """
metadata: {{name: FH008ContentValidation}}
nodes:
  - {{id: ag1, type: agent, name: Browser, properties: {{guardrails: {guardrails}}}}}
  - {{id: t1, type: tool, name: web.fetch, properties: {{allowlist_present: false}}}}
edges:
  - {{id: e1, source: ag1, target: t1, capability: fetchWeb}}
"""


def test_fh008_fires_without_content_validation():
    result = analyze_text(_FH008.format(guardrails="[]"))
    assert "FH-008" in rule_ids(result.findings)


def test_fh008_suppressed_when_agent_has_content_validation():
    result = analyze_text(_FH008.format(guardrails="[contentValidation]"))
    assert "FH-008" not in rule_ids(result.findings)


# --- FH-014: privilege escalation via unscoped delegation --------------------

_FH014 = """
metadata: {{name: Delegation}}
nodes:
  - {{id: ag1, type: agent, name: Planner, properties: {{autonomy_level: full_auto}}}}
  - {{id: ag2, type: agent, name: Privileged, properties: {{trust_level: trusted_core}}}}
edges:
  - {{id: e1, source: ag1, target: ag2, capability: delegateTo, properties: {{has_scoped_delegation: {scoped}}}}}
"""


def test_fh014_fires_on_unscoped_delegation_to_trusted_core():
    result = analyze_text(_FH014.format(scoped="false"))
    assert "FH-014" in rule_ids(result.findings)


def test_fh014_silent_when_delegation_is_scoped():
    result = analyze_text(_FH014.format(scoped="true"))
    assert "FH-014" not in rule_ids(result.findings)


def test_fh014_fires_on_delegation_to_elevated_tool_with_single_agent_count():
    # Delegation can target an elevated-scope tool; the path then has one agent,
    # so the finding must not be over-scored as if two agents were involved.
    yaml_text = """
metadata: {name: ToolEscalation}
nodes:
  - {id: ag1, type: agent, name: Planner, properties: {autonomy_level: full_auto}}
  - {id: t1, type: tool, name: admin.api, properties: {authentication_scope: elevated}}
edges:
  - {id: e1, source: ag1, target: t1, capability: delegateTo}
"""
    findings = analyze_text(yaml_text).findings
    fh014 = next((f for f in findings if f.rule_id == "FH-014"), None)
    assert fh014 is not None
    assert fh014.evidence["target_kind"] == "tool"
    # base high (6.0) + data medium (0.8) + agent_count 1 (0.0) = 6.8; a hard-coded
    # count of 2 would have added 0.3.
    assert fh014.score == 6.8


def test_fh014_elevated_scope_matches_regardless_of_casing():
    # authentication_scope is canonicalised by the normalizer, so a declared
    # "Elevated" must still trigger the tool-escalation branch.
    yaml_text = """
metadata: {name: ElevatedCasing}
nodes:
  - {id: ag1, type: agent, name: Planner, properties: {autonomy_level: full_auto}}
  - {id: t1, type: tool, name: admin.api, properties: {authentication_scope: Elevated}}
edges:
  - {id: e1, source: ag1, target: t1, capability: delegateTo}
"""
    assert "FH-014" in rule_ids(analyze_text(yaml_text).findings)


def test_fh014_silent_when_target_not_privileged():
    yaml_text = """
metadata: {name: NoEscalation}
nodes:
  - {id: ag1, type: agent, name: Planner, properties: {autonomy_level: full_auto}}
  - {id: ag2, type: agent, name: Worker, properties: {trust_level: internal_logic}}
edges:
  - {id: e1, source: ag1, target: ag2, capability: delegateTo}
"""
    assert "FH-014" not in rule_ids(analyze_text(yaml_text).findings)


# --- FH-016: executeCode tool without sandbox isolation ----------------------

_FH016 = """
metadata: {{name: FH016Sandbox}}
nodes:
  - {{id: ag1, type: agent, name: Runner}}
  - {{id: t1, type: tool, name: python.run, properties: {{sandbox_enabled: {sandbox}}}}}
edges:
  - {{id: e1, source: ag1, target: t1, capability: executeCode}}
"""


def test_fh016_fires_when_execute_code_tool_is_unsandboxed():
    result = analyze_text(_FH016.format(sandbox="false"))
    assert "FH-016" in rule_ids(result.findings)


def test_fh016_silent_when_sandbox_enabled():
    result = analyze_text(_FH016.format(sandbox="true"))
    assert "FH-016" not in rule_ids(result.findings)


# --- FH-017: elevated-scope tool reachable from an externally-exposed agent ---

_FH017 = """
metadata: {{name: FH017Exposure}}
nodes:
  - {{id: ag1, type: agent, name: Gateway, properties: {{exposure_boundary: {exposure}}}}}
  - {{id: t1, type: tool, name: admin.api, properties: {{authentication_scope: elevated}}}}
edges:
  - {{id: e1, source: ag1, target: t1, capability: invokeTool}}
"""


def test_fh017_fires_when_external_agent_reaches_elevated_tool():
    result = analyze_text(_FH017.format(exposure="external"))
    assert "FH-017" in rule_ids(result.findings)


def test_fh017_silent_when_agent_is_not_externally_exposed():
    result = analyze_text(_FH017.format(exposure="internal"))
    assert "FH-017" not in rule_ids(result.findings)


# --- FH-018: data asset left at the default (adapter-inferred) sensitivity ----

def test_fh018_fires_when_sensitivity_source_is_default():
    yaml_text = """
metadata: {name: FH018Default}
nodes:
  - {id: a1, type: data_asset, name: UserData, properties: {sensitivity: medium}}
"""
    assert "FH-018" in rule_ids(analyze_text(yaml_text).findings)


def test_fh018_suppressed_when_sensitivity_source_declared_by_config():
    yaml_text = """
metadata: {name: FH018SensitivitySource}
nodes:
  - {id: a1, type: data_asset, name: UserData, properties: {sensitivity: medium, sensitivity_source: declared_by_config}}
"""
    assert "FH-018" not in rule_ids(analyze_text(yaml_text).findings)


# --- FH-019: full-auto agent wired to an unapproved irreversible tool ---------

_FH019 = """
metadata: {{name: FH019Autonomy}}
nodes:
  - {{id: ag1, type: agent, name: AutoAgent, properties: {{autonomy_level: full_auto}}}}
  - {{id: t1, type: tool, name: infra.destroy,
     properties: {{side_effect: true, requires_approval: false, side_effect_reversible: {reversible}}}}}
edges:
  - {{id: e1, source: ag1, target: t1, capability: invokeTool}}
"""


def test_fh019_fires_on_full_auto_agent_with_irreversible_tool():
    result = analyze_text(_FH019.format(reversible="false"))
    assert "FH-019" in rule_ids(result.findings)


def test_fh019_silent_when_tool_is_reversible():
    result = analyze_text(_FH019.format(reversible="true"))
    assert "FH-019" not in rule_ids(result.findings)


# --- FH-020: shared-memory node written without validation -------------------

def test_fh020_fires_when_memory_kind_is_shared_between_agents():
    """FH-020 must fire when memory_kind=shared_between_agents even if scope=user."""
    yaml_text = """
metadata: {name: FH020MemoryKind}
nodes:
  - {id: m1, type: memory, name: SharedPrefs,
     properties: {memory_kind: shared_between_agents, scope: user, write_validated: false}}
"""
    assert "FH-020" in rule_ids(analyze_text(yaml_text).findings)


def test_fh020_silent_when_write_validated():
    """FH-020 must not fire when write_validated=true, regardless of memory_kind."""
    yaml_text = """
metadata: {name: FH020WriteValidated}
nodes:
  - {id: m1, type: memory, name: SharedPrefs,
     properties: {memory_kind: shared_between_agents, scope: user, write_validated: true}}
"""
    assert "FH-020" not in rule_ids(analyze_text(yaml_text).findings)
