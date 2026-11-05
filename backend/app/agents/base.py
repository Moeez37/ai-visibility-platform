import json
import re
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.agents.llm import LLMClient, LLMError

Output = TypeVar("Output", bound=BaseModel)
FENCED_JSON = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)
MAX_ATTEMPTS = 2


class AgentError(Exception):
    def __init__(self, message: str, tokens_used: int = 0):
        super().__init__(message)
        self.tokens_used = tokens_used


@dataclass
class ProfileContext:
    name: str
    domain: str
    industry: str
    description: str
    competitors: list[str] = field(default_factory=list)


@dataclass
class AgentResult(Generic[Output]):
    output: Output
    tokens_used: int


def extract_json(text: str) -> Any:
    candidates = [text.strip()]
    fenced = FENCED_JSON.search(text)
    if fenced:
        candidates.append(fenced.group(1).strip())
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Reply was not valid JSON.")


class BaseAgent(Generic[Output]):
    task: str
    system_prompt: str
    output_schema: type[Output]

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _invoke(self, payload: dict, context: dict | None = None) -> AgentResult[Output]:
        original_message = json.dumps(payload)
        message = original_message
        tokens = 0
        problem = ""

        for _ in range(MAX_ATTEMPTS):
            try:
                reply = self.llm.complete(self.system_prompt, message, self.task)
            except LLMError as error:
                raise AgentError(str(error), tokens) from error
            tokens += reply.tokens
            try:
                data = extract_json(reply.text)
                output = self.output_schema.model_validate(data, context=context)
                return AgentResult(output=output, tokens_used=tokens)
            except (ValueError, ValidationError) as error:
                problem = str(error)
                message = (
                    f"{original_message}\n\nYour previous reply was rejected: {problem}\n"
                    "Reply again with only the corrected JSON object."
                )

        raise AgentError(f"{self.task} returned unusable output: {problem[:300]}", tokens)
