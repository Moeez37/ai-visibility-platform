import hashlib
import json
import re

OFFLINE_MODEL_NAME = "offline-demo"
DOMAIN_PATTERN = re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}\b", re.IGNORECASE)


def _stable_int(text: str, modulo: int) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % modulo


class OfflineClient:
    """Rule-based stand-in for an LLM, so the product runs without an API key."""

    def reply(self, user: str, task: str) -> str:
        payload = json.loads(user.split("\n\nYour previous reply")[0])
        handlers = {
            "query_discovery": self._discover,
            "visibility_scoring": self._score,
            "content_recommendation": self._recommend,
        }
        return json.dumps(handlers[task](payload))

    def _discover(self, payload: dict) -> dict:
        industry = payload["industry"]
        domain = payload["domain"]
        rivals = payload["competitors"] or []
        queries = [
            f"What is the best option for {industry}?",
            f"Which {industry} providers are worth paying for?",
            f"What are the top {industry} options for small teams?",
            f"How much does {industry} usually cost?",
            f"What features matter most in {industry}?",
            f"How do I choose a {industry} provider?",
            f"Is there a free {industry} option that actually works?",
            f"What are common mistakes when buying {industry}?",
            f"Which {industry} providers have the best customer support?",
            f"Is {domain} worth it?",
            f"What are the best alternatives to {domain}?",
        ]
        for rival in rivals[:4]:
            queries.append(f"How does {domain} compare to {rival}?")
            queries.append(f"What are the best alternatives to {rival}?")
        return {"queries": queries[:20]}

    def _score(self, payload: dict) -> dict:
        question = payload["question"]
        domains = DOMAIN_PATTERN.findall(question)
        return {
            "answer_summary": f"Offline demo answer for: {question}",
            "mentions": [{"name": domain, "domain": domain} for domain in domains],
            "estimated_monthly_search_volume": int(10 ** (2 + _stable_int(question, 300) / 100)),
            "competitive_difficulty": 15 + _stable_int(question + "difficulty", 75),
        }

    def _recommend(self, payload: dict) -> dict:
        kinds = ["blog_post", "landing_page", "faq"]
        priorities = ["high", "high", "medium", "medium", "low"]
        recommendations = []
        for index, query in enumerate(payload["queries"][:5]):
            words = [word.strip("?,.").lower() for word in query["query_text"].split()]
            keywords = list(dict.fromkeys(word for word in words if len(word) > 4))[:4]
            recommendations.append(
                {
                    "query_id": query["query_id"],
                    "content_type": kinds[index % len(kinds)],
                    "title": f"{payload['brand']}: answering \"{query['query_text']}\"",
                    "rationale": (
                        f"Offline demo text. This query scores {query['opportunity_score']} "
                        f"and {payload['domain']} does not appear in the answer."
                    ),
                    "target_keywords": keywords or [payload["industry"]],
                    "priority": priorities[index],
                }
            )
        while len(recommendations) < 3:
            recommendations.append(
                {**recommendations[0], "content_type": kinds[len(recommendations)]}
            )
        return {"recommendations": recommendations}
