import json

from app.extensions import db
from app.models import PipelineRun
from tests.conftest import LLM_DOWN, ScriptedLLM, scored, ten_queries, three_recommendations


def _run(client, profile_uuid):
    response = client.post(f"/api/v1/profiles/{profile_uuid}/run")
    assert response.status_code == 202
    return client.get(f"/api/v1/runs/{response.get_json()['run_uuid']}").get_json()


def _queries(client, profile_uuid, query_string=""):
    return client.get(f"/api/v1/profiles/{profile_uuid}/queries{query_string}").get_json()


def test_full_run_stores_scores_and_recommendations(client, use_llm, profile_uuid):
    use_llm(
        ScriptedLLM(ten_queries, lambda _user: scored(), three_recommendations)
    )

    run = _run(client, profile_uuid)

    assert run["status"] == "completed"
    assert run["queries_discovered"] == run["queries_scored"] == 10
    assert run["tokens_used"] == 10 + 100 + 10
    recommendations = client.get(f"/api/v1/profiles/{profile_uuid}/recommendations").get_json()
    assert len(recommendations["items"]) == 3


def test_one_query_failing_does_not_stop_the_run(client, use_llm, profile_uuid):
    def score(user):
        return LLM_DOWN if "number 3" in json.loads(user)["question"] else scored()

    use_llm(ScriptedLLM(ten_queries, score, three_recommendations))

    run = _run(client, profile_uuid)

    assert run["status"] == "completed"
    assert run["queries_scored"] == 9
    assert "1 of 10" in run["error_message"]
    unknown = _queries(client, profile_uuid, "?status=unknown")["items"]
    assert [item["query_text"] for item in unknown] == ["Question number 3?"]
    assert unknown[0]["opportunity_score"] is None


def test_discovery_failure_fails_the_run_with_a_reason(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(lambda _user: LLM_DOWN))

    run = _run(client, profile_uuid)

    assert run["status"] == "failed"
    assert "Could not reach" in run["error_message"]
    assert client.get(f"/api/v1/profiles/{profile_uuid}").get_json()["status"] == "failed"


def test_every_query_failing_fails_the_run(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: LLM_DOWN))

    assert _run(client, profile_uuid)["status"] == "failed"


def test_recommendation_failure_keeps_scored_queries(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: scored(), lambda _user: LLM_DOWN))

    run = _run(client, profile_uuid)

    assert run["status"] == "completed"
    assert "Recommendations could not be generated" in run["error_message"]
    assert _queries(client, profile_uuid)["total"] == 10


def test_visible_everywhere_skips_recommendations(client, use_llm, profile_uuid):
    def fail_if_called(_user):
        raise AssertionError("Agent 3 must not run")

    use_llm(
        ScriptedLLM(ten_queries, lambda _user: scored([("Surfer SEO", None)]), fail_if_called)
    )

    assert _run(client, profile_uuid)["error_message"] is None


def test_failed_rerun_keeps_showing_previous_results(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: scored(), three_recommendations))
    _run(client, profile_uuid)
    use_llm(ScriptedLLM(lambda _user: LLM_DOWN))
    _run(client, profile_uuid)

    assert _queries(client, profile_uuid)["total"] == 10


def test_rerun_replaces_results_instead_of_adding_to_them(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: scored(), three_recommendations))
    _run(client, profile_uuid)
    _run(client, profile_uuid)

    assert _queries(client, profile_uuid)["total"] == 10
    recommendations = client.get(f"/api/v1/profiles/{profile_uuid}/recommendations").get_json()
    assert len(recommendations["items"]) == 3


def test_second_run_is_rejected_while_one_is_running(client, use_llm, profile_uuid):
    db.session.add(PipelineRun(profile_uuid=profile_uuid, llm_model="x", status="running"))
    db.session.commit()

    response = client.post(f"/api/v1/profiles/{profile_uuid}/run")

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "run_in_progress"


def test_recheck_changes_visibility_but_keeps_estimates(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: scored(volume=5000), three_recommendations))
    _run(client, profile_uuid)
    before = _queries(client, profile_uuid)["items"][0]

    use_llm(ScriptedLLM(score=lambda _user: scored([("surferseo.com", "surferseo.com")], volume=1)))
    after = client.post(f"/api/v1/queries/{before['query_uuid']}/recheck").get_json()

    assert after["domain_visible"] is True
    assert after["visibility_position"] == 1
    assert after["estimated_search_volume"] == 5000
    assert after["opportunity_score"] < before["opportunity_score"]


def test_recheck_llm_failure_returns_502_and_changes_nothing(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: scored(), three_recommendations))
    _run(client, profile_uuid)
    before = _queries(client, profile_uuid)["items"][0]

    use_llm(ScriptedLLM(score=lambda _user: LLM_DOWN))
    response = client.post(f"/api/v1/queries/{before['query_uuid']}/recheck")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "llm_error"
    assert _queries(client, profile_uuid)["items"][0] == before
