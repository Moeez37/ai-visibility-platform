from flask import Blueprint, jsonify

from app.api.errors import ApiError
from app.extensions import db
from app.models import DiscoveredQuery
from app.services.pipeline import recheck_query

queries_bp = Blueprint("queries", __name__)


@queries_bp.post("/queries/<query_uuid>/recheck")
def recheck(query_uuid: str):
    query = db.session.get(DiscoveredQuery, query_uuid)
    if query is None:
        raise ApiError(404, "query_not_found", "No query exists with that ID.")
    return jsonify(recheck_query(query).to_dict())
