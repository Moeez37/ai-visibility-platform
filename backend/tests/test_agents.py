import json

import pytest

from app.agents.base import AgentError, ProfileContext, extract_json
from app.agents.discovery import QueryDiscoveryAgent
from app.agents.recommendation import ContentRecommendationAgent, QueryOpportunity
from app.agents.scoring import VisibilityScoringAgent
from tests.conftest import ScriptedLLM, scored, ten_queries

PROFILE = ProfileContext("Surfer SEO", "surferseo.com", "SEO", "desc", ["clearscope.io"])


@pytest.mark.parametrize(
    "reply",
    [
        '{"a": 1}',
        'Here you go:\n```json\n{"a": 1}\n```\nEnjoy!',
        'Sure! {"a": 1} Hope that helps.',
    ],
)
def test_extract_json_handles_wrapped_replies(reply):
    assert extract_json(reply) == {"a": 1}


def test_agent_retries_after_bad_json_and_counts_both_attempts():
    replies = iter(["not json at all", ten_queries()])
    agent = QueryDiscoveryAgent(ScriptedLLM(discovery=lambda _user: next(replies)))

    result = agent.discover(PROFILE)

    assert len(result.output.queries) == 10
    assert result.tokens_used == 20


def test_agent_tells_the_model_what_was_wrong_on_retry():
    seen = []

    def capture(user):
        seen.append(user)
        return "nope" if len(seen) == 1 else ten_queries()

    QueryDiscoveryAgent(ScriptedLLM(discovery=capture)).discover(PROFILE)

    assert "rejected" in seen[1]


def test_agent_raises_after_repeated_bad_output_and_reports_tokens():
    agent = QueryDiscoveryAgent(ScriptedLLM(discovery=lambda _user: {"queries": "wrong type"}))

    with pytest.raises(AgentError) as caught:
        agent.discover(PROFILE)

    assert caught.value.tokens_used == 20


def test_discovery_removes_duplicates_before_counting_the_minimum():
    repeated = {"queries": ["Same question?", "same question? "] * 10}
    agent = QueryDiscoveryAgent(ScriptedLLM(discovery=lambda _user: repeated))

    with pytest.raises(AgentError):
        agent.discover(PROFILE)


def test_discovery_trims_to_twenty():
    many = {"queries": [f"Question {index}?" for index in range(35)]}
    agent = QueryDiscoveryAgent(ScriptedLLM(discovery=lambda _user: many))

    assert len(agent.discover(PROFILE).output.queries) == 20


def _recommendation(query_id):
    return {
        "query_id": query_id,
        "content_type": "faq",
        "title": "T",
        "rationale": "R",
        "target_keywords": ["k"],
        "priority": "low",
    }


def test_recommendation_rejects_query_ids_it_was_not_given():
    bad = {"recommendations": [_recommendation(99)] * 3}
    agent = ContentRecommendationAgent(ScriptedLLM(recommend=lambda _user: bad))

    with pytest.raises(AgentError):
        agent.recommend(PROFILE, [QueryOpportunity(1, "q", 10, 10, 0.5)])


def test_recommendation_trims_to_five():
    many = {"recommendations": [_recommendation(1)] * 8}
    agent = ContentRecommendationAgent(ScriptedLLM(recommend=lambda _user: many))

    result = agent.recommend(PROFILE, [QueryOpportunity(1, "q", 10, 10, 0.5)])

    assert len(result.output.recommendations) == 5


def test_scoring_payload_never_names_the_target_brand():
    seen = []

    def capture(user):
        seen.append(json.loads(user))
        return scored()

    VisibilityScoringAgent(ScriptedLLM(score=capture)).check("Best SEO tool?", PROFILE)

    assert "surfer" not in json.dumps(seen[0]).lower()
