"""Provider compatibility layer (D3; design decision 7).

THE ONLY MODULE THAT KNOWS PROVIDERS EXIST. Provider names, base URLs, and
model defaults live here and nowhere else in agent/ or eval/ — enforced by
tests/test_provider_isolation.py (D3-① as a CI assertion, not a convention).

Contract (decision 7b/3-ii): `call_with_validation` issues a forced function
call, validates the returned arguments against the pydantic wire model, and
retries ONCE with a corrective message on failure. A second failure returns
a degraded result (result=None) — the caller escalates (degraded assessment
-> insufficient_evidence -> gate). Every attempt's metadata (tokens,
latency, status) is returned for trajectory logging; this module never logs
and never sees the trajectory.

Corrective messages carry field paths only, never input values — input
values can contain document text, and while messages legitimately hold
documents (the model must read them), keeping generated text value-free
removes one accidental path into logs (schema invariant 7 defense in depth).
"""

import json
import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel, ValidationError

M = TypeVar("M", bound=BaseModel)

# Provider strings are legal ONLY in this module (hygiene-tested).
_DEFAULTS: dict[str, dict[str, str]] = {
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
}


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    base_url: str
    model: str
    api_key: str


def provider_config(env: Mapping[str, str] | None = None) -> ProviderConfig:
    """Resolve the active provider from environment (D3: switch is config,
    not code). LLM_BASE_URL / LLM_MODEL override the provider defaults."""
    e: Mapping[str, str] = os.environ if env is None else env
    provider = e.get("LLM_PROVIDER", "").strip().lower()
    if provider not in _DEFAULTS:
        raise ValueError(f"LLM_PROVIDER must be one of {sorted(_DEFAULTS)}, got {provider!r}")
    api_key = e.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("LLM_API_KEY is not set")
    defaults = _DEFAULTS[provider]
    return ProviderConfig(
        provider=provider,
        base_url=e.get("LLM_BASE_URL", "").strip() or defaults["base_url"],
        model=e.get("LLM_MODEL", "").strip() or defaults["model"],
        api_key=api_key,
    )


@dataclass(frozen=True)
class RawCompletion:
    """What a completer returns: forced-tool-call arguments (None when the
    response carried no usable tool call) plus token usage."""

    arguments_json: str | None
    tokens_in: int
    tokens_out: int


Completer = Callable[[list[dict[str, Any]], dict[str, Any]], RawCompletion]


def make_completer(cfg: ProviderConfig) -> Completer:
    """Production completer on the openai SDK (both providers speak this
    protocol — that is D3's premise)."""
    from openai import OpenAI

    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

    def complete(messages: list[dict[str, Any]], tool_schema: dict[str, Any]) -> RawCompletion:
        response = client.chat.completions.create(
            model=cfg.model,
            messages=cast(Any, messages),
            tools=cast(Any, [tool_schema]),
            tool_choice={
                "type": "function",
                "function": {"name": tool_schema["function"]["name"]},
            },
        )
        usage = response.usage
        calls = response.choices[0].message.tool_calls
        # getattr: the SDK's union includes custom tool-call types without .function
        function = getattr(calls[0], "function", None) if calls else None
        arguments: str | None = function.arguments if function is not None else None
        return RawCompletion(
            arguments_json=arguments,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
        )

    return complete


@dataclass(frozen=True)
class CallMeta:
    """Per-attempt metadata for the caller's llm_call trajectory events."""

    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    attempt: int
    status: str  # ok | malformed_output | error


@dataclass(frozen=True)
class ValidatedCall(Generic[M]):
    result: M | None
    attempts: list[CallMeta]

    @property
    def degraded(self) -> bool:
        return self.result is None


def _invalid_fields(error: ValidationError) -> str:
    # Field paths only — never input values (see module docstring).
    paths = sorted({".".join(str(part) for part in err["loc"]) for err in error.errors()})
    return ", ".join(paths) or "(root)"


def call_with_validation(
    messages: list[dict[str, Any]],
    model_cls: type[M],
    tool_schema: dict[str, Any],
    completer: Completer,
    cfg: ProviderConfig,
    max_attempts: int = 2,
) -> ValidatedCall[M]:
    """Forced function call -> validate -> one corrective retry -> degrade.

    Mutates `messages` by appending corrective turns so the retry (and any
    later node) sees the failure history — degradation stays visible (D3-②).
    """
    attempts: list[CallMeta] = []
    for attempt in range(1, max_attempts + 1):
        started = time.perf_counter()
        status = "ok"
        parsed: M | None = None
        tokens_in = tokens_out = 0
        try:
            raw = completer(messages, tool_schema)
            tokens_in, tokens_out = raw.tokens_in, raw.tokens_out
            if raw.arguments_json is None:
                status = "malformed_output"
                reason = "response carried no tool call"
            else:
                try:
                    parsed = model_cls.model_validate(json.loads(raw.arguments_json))
                except json.JSONDecodeError:
                    status = "malformed_output"
                    reason = "arguments were not valid JSON"
                except ValidationError as ve:
                    status = "malformed_output"
                    reason = f"invalid fields: {_invalid_fields(ve)}"
        except Exception:
            status = "error"
            reason = "provider call failed"
        latency_ms = int((time.perf_counter() - started) * 1000)
        attempts.append(
            CallMeta(
                provider=cfg.provider,
                model=cfg.model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                attempt=attempt,
                status=status,
            )
        )
        if parsed is not None:
            return ValidatedCall(result=parsed, attempts=attempts)
        if attempt < max_attempts:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Your previous response was not a valid"
                        f" {tool_schema['function']['name']} call ({reason})."
                        " Respond again with exactly one valid call."
                    ),
                }
            )
    return ValidatedCall(result=None, attempts=attempts)
