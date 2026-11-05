import logging

from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.agents.base import AgentError
from app.agents.llm import LLMError
from app.extensions import db

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _error_response(status: int, code: str, message: str, details: list | None = None):
    body = {"error": {"code": code, "message": message, "details": details or []}}
    return jsonify(body), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return _error_response(error.status, error.code, error.message)

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        details = [
            {"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]}
            for item in error.errors()
        ]
        return _error_response(400, "validation_error", "The request is not valid.", details)

    @app.errorhandler(AgentError)
    @app.errorhandler(LLMError)
    def handle_llm_failure(error: Exception):
        db.session.rollback()
        return _error_response(502, "llm_error", str(error))

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return _error_response(error.code or 500, error.name.lower().replace(" ", "_"), error.description or "")

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        logger.exception("Unhandled API error", exc_info=error)
        db.session.rollback()
        return _error_response(500, "internal_error", "Something went wrong on the server.")
