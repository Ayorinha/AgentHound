"""Structured event logging (spec section 14).

Emits one JSON line per event with ``analysis_id``, ``timestamp``, ``event`` and
``metadata``. Full prompts and sensitive data are never logged; callers pass
only redacted counts/identifiers as metadata.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

_logger = logging.getLogger("agenthound")
# Set level and propagation unconditionally so they hold even if another part of
# the process configured this logger first. Do not propagate to the root/uvicorn
# loggers, which would otherwise emit each event line a second time.
_logger.setLevel(logging.INFO)
_logger.propagate = False
# Add the handler only once to avoid duplicate output on re-import.
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)

# Canonical event names (spec section 14).
ANALYSIS_STARTED = "analysis_started"
ANALYSIS_COMPLETED = "analysis_completed"
PARSER_SELECTED = "parser_selected"
NORMALIZATION_WARNINGS = "normalization_warnings"
RULES_EXECUTED = "rules_executed"
FINDINGS_GENERATED = "findings_generated"
SIMULATION_STARTED = "simulation_started"
SIMULATION_COMPLETED = "simulation_completed"


def log_event(event: str, analysis_id: str, **metadata: Any) -> None:
    record = {
        "analysis_id": analysis_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "metadata": metadata,
    }
    # default=str keeps logging best-effort: a non-JSON-serializable metadata
    # value (Path, enum, datetime, ...) is stringified rather than raising and
    # failing the request.
    _logger.info(json.dumps(record, default=str))
