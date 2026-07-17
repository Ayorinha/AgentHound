from datetime import datetime
from pathlib import Path

from app.logging_util import log_event


def test_log_event_tolerates_non_serializable_metadata():
    # Must not raise even when metadata holds non-JSON-serializable values;
    # logging is best-effort and cannot be allowed to fail the request.
    log_event(
        "analysis_started",
        "analysis-1",
        some_path=Path("C:/tmp/x"),
        when=datetime.now(),
    )
