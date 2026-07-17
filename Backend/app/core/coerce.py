"""Small, dependency-free value coercions shared across layers.

Both the parser (at ingestion, where raw YAML values first enter the IR) and the
rule engine (reading pass-through properties from hand-authored generic YAML)
need to interpret booleans safely. Keeping the helper here — with no imports of
its own — lets both layers use it without the parser having to depend on the
rules package.
"""

from __future__ import annotations

_TRUE_STRINGS = {"true", "1", "yes", "on"}


def as_bool(value: object) -> bool:
    """Coerce a property value to a bool, tolerating string forms from YAML.

    A hand-authored architecture may quote a boolean (``sandbox_enabled:
    "false"``); raw truthiness would read that non-empty string as ``True`` and
    silently suppress a finding. Because suppression is the dangerous direction
    for a security scanner, this normalises common string forms explicitly:
    recognised true-strings are true, every other string is false, and non-string
    values fall back to plain ``bool``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_STRINGS
    return bool(value)
