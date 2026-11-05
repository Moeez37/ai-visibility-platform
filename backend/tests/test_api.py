import pytest

from tests.conftest import ScriptedLLM, scored, ten_queries, three_recommendations


@pytest.mark.parametrize(
    "domain",
    ["http://example.com", "example", "example.com/path", "exa mple.com", ""],
)
def test_profile_rejects_bad_domains_with_the_standard_error_shape(client, domain):
    response = client.post(
        "/api/v1/profiles",
        json={"name": "A", "domain": domain, "industry": "B", "description": "C"},
    )

    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "domain"


@pytest.mark.parametrize(
    "path, method",
    [
        ("/api/v1/profiles/missing", "get"),
        ("/api/v1/profiles/missing/run", "post"),
        ("/api/v1/profiles/missing/queries", "get"),
        ("/api/v1/profiles/missing/recommendations", "get"),
        ("/api/v1/queries/missing/recheck", "post"),
        ("/api/v1/runs/missing", "get"),
        ("/api/v1/nothing-here", "get"),
    ],
)
def test_unknown_resources_return_json_404(client, path, method):
    response = getattr(client, method)(path)

    assert response.status_code == 404
    assert "code" in response.get_json()["error"]


@pytest.mark.parametrize(
    "query_string",
    ["?min_score=2", "?min_score=abc", "?status=maybe", "?page=0", "?per_page=1000"],
)
def test_query_filters_reject_bad_values(client, profile_uuid, query_string):
    response = client.get(f"/api/v1/profiles/{profile_uuid}/queries{query_string}")

    assert response.status_code == 400


def test_query_filters_and_pagination(client, use_llm, profile_uuid):
    def score(user):
        if "number 0" in user:
            return scored([("Surfer SEO", None)], volume=90000, difficulty=5)
        if "number 1" in user:
            return scored(volume=90000, difficulty=5)
        return scored(volume=10, difficulty=95)

    use_llm(ScriptedLLM(ten_queries, score, three_recommendations))
    client.post(f"/api/v1/profiles/{profile_uuid}/run")
    url = f"/api/v1/profiles/{profile_uuid}/queries"

    first_page = client.get(f"{url}?page=1&per_page=4").get_json()
    assert (first_page["total"], first_page["pages"], len(first_page["items"])) == (10, 3, 4)
    assert first_page["items"][0]["query_text"] == "Question number 1?"

    visible = client.get(f"{url}?status=visible").get_json()["items"]
    assert [item["query_text"] for item in visible] == ["Question number 0?"]

    high_score = client.get(f"{url}?min_score=0.7").get_json()["items"]
    assert [item["query_text"] for item in high_score] == ["Question number 1?"]


def test_dashboard_summary_counts_real_rows(client, use_llm, profile_uuid):
    use_llm(ScriptedLLM(ten_queries, lambda _user: scored(), three_recommendations))
    client.post(f"/api/v1/profiles/{profile_uuid}/run")

    summary = client.get("/api/v1/dashboard/summary").get_json()

    assert summary["total_profiles"] == 1
    assert summary["total_queries"] == 10
    assert 0 < summary["avg_opportunity_score"] <= 1
    assert summary["recent_runs"][0]["profile_name"] == "Surfer SEO"


def test_offline_provider_runs_the_real_pipeline_end_to_end(app, client, profile_uuid):
    app.config.update(LLM_PROVIDER="offline")

    run = client.post(f"/api/v1/profiles/{profile_uuid}/run").get_json()
    run = client.get(f"/api/v1/runs/{run['run_uuid']}").get_json()

    assert run["status"] == "completed"
    assert run["llm_model"] == "offline-demo"
    assert 10 <= run["queries_discovered"] <= 20
    items = client.get(f"/api/v1/profiles/{profile_uuid}/queries?per_page=100").get_json()["items"]
    assert any(item["domain_visible"] for item in items)
    assert any(item["domain_visible"] is False for item in items)
    recommendations = client.get(f"/api/v1/profiles/{profile_uuid}/recommendations").get_json()
    assert 3 <= len(recommendations["items"]) <= 5
