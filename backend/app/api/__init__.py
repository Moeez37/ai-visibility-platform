from flask import Flask

from app.api.errors import register_error_handlers
from app.api.profiles import profiles_bp
from app.api.queries import queries_bp
from app.api.runs import runs_bp


def register_api(app: Flask) -> None:
    for blueprint in (profiles_bp, queries_bp, runs_bp):
        app.register_blueprint(blueprint, url_prefix="/api/v1")
    register_error_handlers(app)
