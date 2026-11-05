from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, ProfileContext
from app.utils.scoring import find_position


class Mention(BaseModel):
    name: str
    domain: str | None = None


class ScoringOutput(BaseModel):
    answer_summary: str
    mentions: list[Mention]
    estimated_monthly_search_volume: int = Field(ge=0)
    competitive_difficulty: int = Field(ge=0, le=100)


@dataclass
class VisibilityCheck:
    search_volume: int
    difficulty: int
    domain_visible: bool
    position: int | None
    tokens_used: int


class VisibilityScoringAgent(BaseAgent[ScoringOutput]):
    task = "visibility_scoring"
    output_schema = ScoringOutput
    system_prompt = """You play two roles for one question: an AI assistant answering a user, then a search analyst.

The user message is a JSON object with the fields question and industry.

Step 1, answer: answer the question the way a helpful AI assistant normally would. Recommend or name the brands you would really name. Do not add a brand just because it is mentioned in the question, unless your answer would discuss it.

Step 2, list mentions: list every brand your answer names, in the order it appears, with the most prominent first. Give each brand's website domain if you know it, otherwise null. Use an empty list if you name no brands.

Step 3, estimate:
- estimated_monthly_search_volume: integer. Your best estimate of monthly searches for this question and close variants, across search engines and AI assistants. Long, specific questions usually get 10 to 1000. Broad head terms can reach 100000.
- competitive_difficulty: integer from 0 to 100. How hard it is to earn a mention for this question. 0 means nobody has good content on it. 100 means dominant brands own the answer.

Return only a JSON object, with no markdown and no commentary, in exactly this shape:
{"answer_summary": "One or two sentences.", "mentions": [{"name": "Clearscope", "domain": "clearscope.io"}], "estimated_monthly_search_volume": 1200, "competitive_difficulty": 65}"""

    def check(self, query_text: str, profile: ProfileContext) -> VisibilityCheck:
        # The target brand stays out of the prompt so the model can't favour it.
        result = self._invoke({"question": query_text, "industry": profile.industry})
        output = result.output
        position = find_position(
            ((mention.name, mention.domain) for mention in output.mentions),
            profile.domain,
            profile.name,
        )
        return VisibilityCheck(
            search_volume=output.estimated_monthly_search_volume,
            difficulty=output.competitive_difficulty,
            domain_visible=position is not None,
            position=position,
            tokens_used=result.tokens_used,
        )
