from flask import Blueprint, jsonify, request
from sqlalchemy import case

from app.api.errors import ApiError
from app.api.schemas import ProfileCreate, QueryFilters
from app.extensions import db
from app.models import BusinessProfile, ContentRecommendation, DiscoveredQuery, PipelineRun
from app.services.pipeline import fail_stale_runs, start_run

profiles_bp = Blueprint("profiles", __name__)


def _get_profile(profile_uuid: str) -> BusinessProfile:
    profile = db.session.get(BusinessProfile, profile_uuid)
    if profile is None:
        raise ApiError(404, "profile_not_found", "No profile exists with that ID.")
    return profile


def _results_run_uuid(profile_uuid: str) -> str | None:
    # Show the newest finished run that produced queries, so a failed re-run hides nothing.
    run = (
        PipelineRun.query.filter(
            PipelineRun.profile_uuid == profile_uuid,
            PipelineRun.status != "running",
            PipelineRun.queries_discovered > 0,
        )
        .order_by(PipelineRun.started_at.desc())
        .first()
    )
    return run.uuid if run else None


@profiles_bp.post("/profiles")
def create_profile():
    data = ProfileCreate.model_validate(request.get_json())
    profile = BusinessProfile(**data.model_dump())
    db.session.add(profile)
    db.session.commit()
    return jsonify(profile.to_dict()), 201


@profiles_bp.get("/profiles")
def list_profiles():
    profiles = BusinessProfile.query.order_by(BusinessProfile.created_at.desc()).all()
    return jsonify({"items": [profile.to_dict() for profile in profiles]})


@profiles_bp.get("/profiles/<profile_uuid>")
def get_profile(profile_uuid: str):
    return jsonify(_get_profile(profile_uuid).to_dict())


@profiles_bp.post("/profiles/<profile_uuid>/run")
def run_pipeline(profile_uuid: str):
    profile = _get_profile(profile_uuid)
    fail_stale_runs(profile_uuid)
    already_running = PipelineRun.query.filter_by(
        profile_uuid=profile_uuid, status="running"
    ).first()
    if already_running:
        raise ApiError(409, "run_in_progress", "A pipeline run is already in progress.")
    return jsonify(start_run(profile).to_dict()), 202


@profiles_bp.get("/profiles/<profile_uuid>/queries")
def list_queries(profile_uuid: str):
    _get_profile(profile_uuid)
    filters = QueryFilters.model_validate(request.args.to_dict())

    query = DiscoveredQuery.query.filter_by(run_uuid=_results_run_uuid(profile_uuid))
    if filters.min_score is not None:
        query = query.filter(DiscoveredQuery.opportunity_score >= filters.min_score)
    if filters.status == "unknown":
        query = query.filter(DiscoveredQuery.domain_visible.is_(None))
    elif filters.status:
        query = query.filter(DiscoveredQuery.domain_visible.is_(filters.status == "visible"))

    page = query.order_by(
        DiscoveredQuery.opportunity_score.is_(None),
        DiscoveredQuery.opportunity_score.desc(),
    ).paginate(page=filters.page, per_page=filters.per_page, error_out=False)
    return jsonify(
        {
            "items": [item.to_dict() for item in page.items],
            "page": page.page,
            "per_page": page.per_page,
            "total": page.total,
            "pages": page.pages,
        }
    )


@profiles_bp.get("/profiles/<profile_uuid>/recommendations")
def list_recommendations(profile_uuid: str):
    _get_profile(profile_uuid)
    priority_order = case({"high": 0, "medium": 1, "low": 2}, value=ContentRecommendation.priority)
    items = (
        ContentRecommendation.query.join(DiscoveredQuery)
        .filter(DiscoveredQuery.run_uuid == _results_run_uuid(profile_uuid))
        .order_by(priority_order, ContentRecommendation.created_at)
        .all()
    )
    return jsonify({"items": [item.to_dict() for item in items]})
