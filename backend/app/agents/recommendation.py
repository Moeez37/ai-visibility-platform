from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.agents.base import AgentResult, BaseAgent, ProfileContext

MIN_RECOMMENDATIONS = 3
MAX_RECOMMENDATIONS = 5


class Recommendation(BaseModel):
    query_id: int
    content_type: Literal["blog_post", "landing_page", "faq"]
    title: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    target_keywords: list[str] = Field(min_length=1)
    priority: Literal["high", "medium", "low"]

    @field_validator("query_id")
    @classmethod
    def query_must_exist(cls, value: int, info: ValidationInfo) -> int:
        if value not in info.context["query_ids"]:
            raise ValueError(f"query_id {value} was not in the input.")
        return value


class RecommendationOutput(BaseModel):
    recommendations: list[Recommendation] = Field(min_length=MIN_RECOMMENDATIONS)


@dataclass
class QueryOpportunity:
    query_id: int
    query_text: str
    search_volume: int
    difficulty: int
    opportunity_score: float


class ContentRecommendationAgent(BaseAgent[RecommendationOutput]):
    task = "content_recommendation"
    output_schema = RecommendationOutput
    system_prompt = f"""You are a content strategist who helps businesses get named in AI-generated answers.

The user message is a JSON object with the business (brand, domain, industry, description, competitors) and queries: questions where AI assistants do not mention this business, each with query_id, query_text, search_volume, difficulty and opportunity_score.

Write {MIN_RECOMMENDATIONS} to {MAX_RECOMMENDATIONS} content recommendations.

Rules:
- Each one targets exactly one query_id from the input. Favour higher opportunity_score.
- content_type is one of: blog_post, landing_page, faq.
- title is the actual headline to publish, specific enough to brief a writer. Not a topic such as "Write about SEO".
- rationale says in one or two sentences why this piece would earn a mention for that query, using the numbers or the competitive situation.
- target_keywords lists 3 to 6 specific phrases to target.
- priority is high, medium or low. Use high only for the best one or two.
- Do not invent facts, customers or statistics about the business.

Return only a JSON object, with no markdown and no commentary, in exactly this shape:
{{"recommendations": [{{"query_id": 1, "content_type": "blog_post", "title": "Clearscope vs Surfer SEO: Which Fits a Small Content Team?", "rationale": "High volume and no mention today. Comparison pages are often cited in answers to this kind of question.", "target_keywords": ["clearscope vs surfer seo", "seo content tool comparison", "best content optimization tool"], "priority": "high"}}]}}"""

    def recommend(
        self, profile: ProfileContext, opportunities: list[QueryOpportunity]
    ) -> AgentResult[RecommendationOutput]:
        result = self._invoke(
            {
                "brand": profile.name,
                "domain": profile.domain,
                "industry": profile.industry,
                "description": profile.description,
                "competitors": profile.competitors,
                "queries": [vars(opportunity) for opportunity in opportunities],
            },
            context={"query_ids": {opportunity.query_id for opportunity in opportunities}},
        )
        result.output.recommendations = result.output.recommendations[:MAX_RECOMMENDATIONS]
        return result
