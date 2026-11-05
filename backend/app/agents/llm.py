from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

import anthropic
import openai

from app.agents.offline import OfflineClient, OFFLINE_MODEL_NAME

MAX_OUTPUT_TOKENS = 16000
REQUEST_TIMEOUT_SECONDS = 120


class LLMError(Exception):
    pass


@dataclass
class LLMReply:
    text: str
    tokens: int


class LLMClient(Protocol):
    model_name: str

    def complete(self, system: str, user: str, task: str) -> LLMReply: ...


class AnthropicClient:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.model_name = f"anthropic:{model}"
        self.client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    def complete(self, system: str, user: str, task: str) -> LLMReply:
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as error:
            raise LLMError("Anthropic rejected the API key.") from error
        except anthropic.RateLimitError as error:
            raise LLMError("Anthropic rate limit reached.") from error
        except anthropic.APIStatusError as error:
            raise LLMError(f"Anthropic returned HTTP {error.status_code}.") from error
        except anthropic.APIConnectionError as error:
            raise LLMError("Could not reach Anthropic.") from error

        tokens = response.usage.input_tokens + response.usage.output_tokens
        if response.stop_reason == "refusal":
            raise LLMError("Anthropic declined the request.")
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMReply(text=text, tokens=tokens)


class OpenAIClient:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.model_name = f"openai:{model}"
        self.client = openai.OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    def complete(self, system: str, user: str, task: str) -> LLMReply:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=MAX_OUTPUT_TOKENS,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except openai.AuthenticationError as error:
            raise LLMError("OpenAI rejected the API key.") from error
        except openai.RateLimitError as error:
            raise LLMError("OpenAI rate limit reached.") from error
        except openai.APIStatusError as error:
            raise LLMError(f"OpenAI returned HTTP {error.status_code}.") from error
        except openai.APIConnectionError as error:
            raise LLMError("Could not reach OpenAI.") from error

        tokens = response.usage.total_tokens if response.usage else 0
        return LLMReply(text=response.choices[0].message.content or "", tokens=tokens)


class OfflineLLM:
    model_name = OFFLINE_MODEL_NAME

    def __init__(self):
        self.client = OfflineClient()

    def complete(self, system: str, user: str, task: str) -> LLMReply:
        return LLMReply(text=self.client.reply(user, task), tokens=0)


def build_llm_client(config: Mapping) -> LLMClient:
    provider = config["LLM_PROVIDER"]
    anthropic_key = config["ANTHROPIC_API_KEY"]
    openai_key = config["OPENAI_API_KEY"]

    if provider == "auto":
        provider = "anthropic" if anthropic_key else "openai" if openai_key else "offline"
    if provider == "anthropic" and anthropic_key:
        return AnthropicClient(anthropic_key, config["ANTHROPIC_MODEL"])
    if provider == "openai" and openai_key:
        return OpenAIClient(openai_key, config["OPENAI_MODEL"])
    if provider == "offline":
        return OfflineLLM()
    raise LLMError(f"LLM_PROVIDER is '{provider}' but no matching API key is set.")
