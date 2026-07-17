"""GET /analyses/{analysis_id}/graph (spec section 12.2)."""

from __future__ import annotations

from fastapi import APIRouter

from ...core.graph.serializer import serialize_graph
from ...core.storage.repository import repository
from ..errors import as_http_error

router = APIRouter()


# Plain def (not async): synchronous repository read + serialization, so FastAPI
# runs it in its threadpool rather than blocking the event loop.
@router.get("/analyses/{analysis_id}/graph", summary="Get the normalized graph for the frontend")
def get_graph(analysis_id: str) -> dict:
    result = repository.get(analysis_id)
    if result is None:
        raise as_http_error("ANALYSIS_NOT_FOUND", f"No analysis {analysis_id}.", status_code=404)
    return serialize_graph(result.ir, result.findings)
