from flask import Blueprint, jsonify
from sqlalchemy import func

from app.api.errors import ApiError
from app.extensions import db
from app.models import BusinessProfile, DiscoveredQuery, PipelineRun

runs_bp = Blueprint("runs", __name__)
RECENT_RUN_LIMIT = 10


@runs_bp.get("/runs/<run_uuid>")
def get_run(run_uuid: str):
    run = db.session.get(PipelineRun, run_uuid)
    if run is None:
        raise ApiError(404, "run_not_found", "No pipeline run exists with that ID.")
    return jsonify(run.to_dict())


@runs_bp.get("/dashboard/summary")
def dashboard_summary():
    average = db.session.query(func.avg(DiscoveredQuery.opportunity_score)).scalar()
    recent_runs = PipelineRun.query.order_by(PipelineRun.started_at.desc()).limit(RECENT_RUN_LIMIT)
    return jsonify(
        {
            "total_profiles": db.session.query(func.count(BusinessProfile.uuid)).scalar(),
            "total_queries": db.session.query(func.count(DiscoveredQuery.uuid)).scalar(),
            "avg_opportunity_score": round(average, 3) if average is not None else None,
            "recent_runs": [run.to_dict() for run in recent_runs],
        }
    )
