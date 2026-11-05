import json

import pytest

from app import create_app
from app.agents.llm import LLMError, LLMReply
from app.extensions import db


class ScriptedLLM:
    model_name = "scripted"

    def __init__(self, discovery=None, score=None, recommend=None):
        self.discovery = discovery
        self.score = score
        self.recommend = recommend

    def complete(self, system, user, task):
        handler = {
            "query_discovery": self.discovery,
            "visibility_scoring": self.score,
            "content_recommendation": self.recommend,
        }[task]
        result = handler(user)
        if isinstance(result, Exception):
            raise result
        text = result if isinstance(result, str) else json.dumps(result)
        return LLMReply(text=text, tokens=10)


def ten_queries(_user=None):
    return {"queries": [f"Question number {index}?" for index in range(10)]}


def scored(mentions=(), volume=1000, difficulty=50):
    return {
        "answer_summary": "summary",
        "mentions": [{"name": name, "domain": domain} for name, domain in mentions],
        "estimated_monthly_search_volume": volume,
        "competitive_difficulty": difficulty,
    }


def three_recommendations(user):
    query_id = json.loads(user.split("\n\n")[0])["queries"][0]["query_id"]
    item = {
        "query_id": query_id,
        "content_type": "faq",
        "title": "Title",
        "rationale": "Why",
        "target_keywords": ["keyword"],
        "priority": "high",
    }
    return {"recommendations": [item, item, item]}


LLM_DOWN = LLMError("Could not reach the provider.")


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "PIPELINE_ASYNC": False,
            "SCORING_CONCURRENCY": 2,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def use_llm(monkeypatch):
    def install(llm):
        monkeypatch.setattr("app.services.pipeline.build_llm_client", lambda _config: llm)

    return install


@pytest.fixture
def profile_uuid(client):
    response = client.post(
        "/api/v1/profiles",
        json={
            "name": "Surfer SEO",
            "domain": "surferseo.com",
            "industry": "SEO Software",
            "description": "SEO content tool",
            "competitors": ["clearscope.io"],
        },
    )
    return response.get_json()["profile_uuid"]
