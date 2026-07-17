"""Control recommendation and simulation endpoints (spec sections 12.5-12.6)."""

from __future__ import annotations

from fastapi import APIRouter

from ...core.controls import recommender, simulator
from ...core.ir.models import SimulateControlsRequest
from ...core.storage.repository import repository
from ..errors import as_http_error

router = APIRouter()


# Plain def (not async): synchronous repository read plus graph/rule recompute,
# so FastAPI runs it in its threadpool rather than blocking the event loop.
@router.get(
    "/analyses/{analysis_id}/controls/recommendations",
    summary="Recommend controls, ranked by estimated risk reduction",
    tags=["controls"],
)
def get_recommendations(analysis_id: str) -> dict:
    result = repository.get(analysis_id)
    if result is None:
        raise as_http_error("ANALYSIS_NOT_FOUND", f"No analysis {analysis_id}.", status_code=404)
    return recommender.recommend(result)


@router.post(
    "/analyses/{analysis_id}/simulate-controls",
    summary="Simulate applying controls and return before/after risk",
    tags=["controls"],
)
def simulate_controls(analysis_id: str, request: SimulateControlsRequest) -> dict:
    result = repository.get(analysis_id)
    if result is None:
        raise as_http_error("ANALYSIS_NOT_FOUND", f"No analysis {analysis_id}.", status_code=404)
    # Unknown control ids / target nodes raise IRValidationError (mapped to 400).
    return simulator.simulate(result, request.controls_to_apply)
