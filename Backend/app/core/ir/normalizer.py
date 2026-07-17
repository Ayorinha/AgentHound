"""IR normalization: apply safe node-property defaults.

Spec section 4.2 (safe defaults). The tool name -> capability mapping helpers
(spec section 6) are defined here for use by future framework adapters, but in
Phase 1 they are not applied to edges: the generic format declares edge
capabilities explicitly, so ``normalize()`` only fills node-property defaults.
"""

from __future__ import annotations

from ..catalogs import default_properties
from ..coerce import as_bool
from .models import AnalysisIR, Node

# Concrete tool name -> generic capability verbs (spec section 6).
# Keys match on the tool name/id (case-insensitive, exact or suffix).
TOOL_CAPABILITY_MAP: dict[str, list[str]] = {
    "gmail.send": ["send", "invokeTool"],
    "slack.postmessage": ["send", "invokeTool"],
    "calendar.create": ["createResource", "invokeTool"],
    "calendar.update": ["modifyResource", "invokeTool"],
    "browser.visit": ["fetchWeb"],
    "requests.get": ["fetchWeb"],
    "linkedin.fetch": ["fetchWeb"],
    "db.query": ["read"],
    "ats.query": ["read", "search"],
    "pdf.parse": ["read", "extractInformation"],
    "python.run": ["executeCode"],
    "shell.run": ["executeCode"],
}


def capabilities_for_tool(tool_name: str) -> list[str]:
    """Best-effort mapping of a concrete tool name to generic capabilities.

    Falls back to ``["invokeTool"]`` when the name is unknown.
    """
    key = tool_name.strip().lower()
    if key in TOOL_CAPABILITY_MAP:
        return list(TOOL_CAPABILITY_MAP[key])
    for known, caps in TOOL_CAPABILITY_MAP.items():
        if key.endswith(known) or known in key:
            return list(caps)
    return ["invokeTool"]


# Scalar enum-valued properties (spec section 4.2 enums). These are lowercase in
# the catalog and in the spec, but a hand-authored architecture may vary the
# casing/whitespace (e.g. ``sensitivity: High``). Canonicalising them once here
# keeps every rule's comparison robust -- and matters for safety: a mistyped
# ``trust_level: Untrusted`` or ``sensitivity: High`` would otherwise silently
# drop findings.
_ENUM_PROPERTIES = (
    "trust_level",
    "sensitivity",
    "boundary",
    "target_boundary",
    "autonomy_level",
    "exposure_boundary",
    "authentication_scope",
    "access_scope",
    "recipient_type",
    "scope",
    "status",
    "effect",
)


def _apply_node_defaults(node: Node) -> Node:
    """Return a node whose missing properties are filled with safe defaults.

    Declared properties always win over defaults; property values are then
    canonicalised so every rule sees clean types regardless of how the source
    was authored: scalar enums are lowercased/trimmed, and any property whose
    catalog default is a boolean is coerced with ``as_bool`` (so a quoted
    ``"false"`` cannot read as truthy and silently suppress a finding).
    """
    defaults = default_properties(node.type.value)
    merged = dict(defaults)
    merged.update(node.properties or {})
    # Coerce booleans by consulting the catalog default's type -- this covers
    # every declared bool property (requires_approval, sandbox_enabled,
    # approval_gate_present, contains_pii, ...) without a hand-maintained list.
    for key, default_value in defaults.items():
        if isinstance(default_value, bool) and key in merged:
            merged[key] = as_bool(merged[key])
    for key in _ENUM_PROPERTIES:
        value = merged.get(key)
        if isinstance(value, str):
            merged[key] = value.strip().lower()
    node.properties = merged
    return node


def normalize(ir: AnalysisIR) -> AnalysisIR:
    """Fill safe defaults on every node in place and return the IR.

    Edges are left as authored; capability validation happens in ``validators``.
    """
    for node in ir.nodes:
        _apply_node_defaults(node)
    return ir
