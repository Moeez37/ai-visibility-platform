from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(config_overrides or {})

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    return app
