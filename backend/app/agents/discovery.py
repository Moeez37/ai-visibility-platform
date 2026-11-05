from pydantic import BaseModel, field_validator

from app.agents.base import AgentResult, BaseAgent, ProfileContext

MIN_QUERIES = 10
MAX_QUERIES = 20


class DiscoveryOutput(BaseModel):
    queries: list[str]

    @field_validator("queries")
    @classmethod
    def dedupe_and_bound(cls, queries: list[str]) -> list[str]:
        unique = {query.strip().casefold(): query.strip() for query in reversed(queries) if query.strip()}
        cleaned = list(reversed(unique.values()))
        if len(cleaned) < MIN_QUERIES:
            raise ValueError(f"Need at least {MIN_QUERIES} distinct queries, got {len(cleaned)}.")
        return cleaned[:MAX_QUERIES]


class QueryDiscoveryAgent(BaseAgent[DiscoveryOutput]):
    task = "query_discovery"
    output_schema = DiscoveryOutput
    system_prompt = f"""You research how real people use AI assistants such as ChatGPT, Claude and Perplexity to choose products and services.

The user message is a JSON business profile with the fields brand, domain, industry, description and competitors.

Write {MIN_QUERIES} to {MAX_QUERIES} questions a potential customer would type into an AI assistant.

Rules:
- Write each question in natural spoken language, the way a person asks, not as a search keyword.
- Cover a mix of intents: "best tool" lists, direct comparisons, alternatives to a competitor, pricing, how to choose, and problems the product solves.
- At least half of the questions must not name any brand. These show whether the business is found by people who don't know it yet.
- At most a quarter may name the target brand. Comparison questions should use real competitor names from the profile.
- Be specific to this industry. Avoid questions that could apply to any business.
- Do not repeat a question in different words.

Return only a JSON object, with no markdown and no commentary, in exactly this shape:
{{"queries": ["What is the best SEO content tool?", "How does Surfer SEO compare to Clearscope?"]}}"""

    def discover(self, profile: ProfileContext) -> AgentResult[DiscoveryOutput]:
        return self._invoke(
            {
                "brand": profile.name,
                "domain": profile.domain,
                "industry": profile.industry,
                "description": profile.description,
                "competitors": profile.competitors,
            }
        )
