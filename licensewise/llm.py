"""Groq (open-weight models) chat calls that return validated Pydantic objects.

Free-tier limits are per model: about 8,000 tokens/minute and 1,000 requests/day.
The Groq SDK retries 429s using the server's retry-after header.
"""

import os
from collections import Counter

from dotenv import load_dotenv
from groq import APIStatusError, Groq
from pydantic import BaseModel, ValidationError

from licensewise import ROOT

PIPELINE_MODEL = "openai/gpt-oss-120b"     # Stage 1 and Stage 2
DESCRIPTION_MODEL = "qwen/qwen3.8-27b"     # writes test descriptions (a different family)
CHECK_MODEL = "openai/gpt-oss-20b"         # round-trip check of test descriptions

USAGE = Counter()  # tokens per model for this process
_client = None


def client():
    global _client
    if _client is None:
        load_dotenv(ROOT / ".env")
        if not os.environ.get("GROQ_API_KEY"):
            raise SystemExit("GROQ_API_KEY is not set (expected in .env at the project root).")
        _client = Groq(max_retries=8)
    return _client


def _strict_schema(model: type[BaseModel]) -> dict:
    """Pydantic JSON schema with additionalProperties: false on every object (strict mode)."""
    schema = model.model_json_schema()

    def close(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for value in node.values():
                close(value)
        elif isinstance(node, list):
            for value in node:
                close(value)

    close(schema)
    return schema


def _reasoning_args(model):
    if model.startswith("openai/gpt-oss"):
        return {"reasoning_effort": "medium"}
    return {}


def complete_json(model: str, system: str, user: str, output: type[BaseModel],
                  max_tokens: int = 8000) -> BaseModel:
    """One chat call constrained to `output`'s schema; retries once if validation fails."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    response_format = {"type": "json_schema",
                       "json_schema": {"name": output.__name__, "schema": _strict_schema(output),
                                       "strict": True}}
    last_error = None
    for _ in range(2):
        try:
            response = client().chat.completions.create(
                model=model, messages=messages, response_format=response_format,
                max_completion_tokens=max_tokens, **_reasoning_args(model))
        except APIStatusError as e:
            # 413: prompt + output cap exceeds the free tier's tokens-per-minute; retry smaller.
            if e.status_code != 413 or max_tokens <= 3000:
                raise
            max_tokens = 3000
            continue
        USAGE[f"{model} input"] += response.usage.prompt_tokens
        USAGE[f"{model} output"] += response.usage.completion_tokens
        try:
            return output.model_validate_json(response.choices[0].message.content or "")
        except ValidationError as e:
            last_error = e
    raise ValueError(f"{model} returned invalid {output.__name__}: {last_error}")
