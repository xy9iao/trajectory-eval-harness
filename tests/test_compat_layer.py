"""Compat-layer contract tests (design decision 7; D3's three requirements).

Mocked transport only — zero live calls, zero keys in CI. The provider
matrix runs the SAME chain under both provider configs: ok path, malformed
-> corrective retry -> ok, and malformed x2 -> degraded (the client half of
decision 3-ii's escalation; the gate half is asserted from Stage G on).
"""

import json
from typing import Any

import pytest

from agent.client import (
    ProviderConfig,
    RawCompletion,
    call_with_validation,
    provider_config,
)
from agent.types import SubmitAssessment, submit_assessment_tool

PROVIDERS = ["deepseek", "openai"]  # test data; isolation rule covers agent/ + eval/ only

VALID_ARGS = {
    "dimension": "skills_coverage",
    "score": 2,
    "evidence_quotes": [{"doc": "resume", "quote": "built Spark pipelines"}],
    "determinations": [{"requirement": "Spark", "value": "partial"}],
    "notes": "",
}


def _cfg(provider: str) -> ProviderConfig:
    return provider_config({"LLM_PROVIDER": provider, "LLM_API_KEY": "test-key-not-real"})


def _completer(responses: list[str | None]) -> Any:
    """Scripted completer: pops one canned response per attempt."""
    calls: list[list[dict[str, Any]]] = []

    def complete(messages: list[dict[str, Any]], tool_schema: dict[str, Any]) -> RawCompletion:
        calls.append(list(messages))
        return RawCompletion(arguments_json=responses.pop(0), tokens_in=100, tokens_out=20)

    complete.calls = calls  # type: ignore[attr-defined]
    return complete


# --- provider config (D3-③: switch is env, not code) ---


@pytest.mark.parametrize("provider", PROVIDERS)
def test_provider_config_resolves_defaults(provider: str) -> None:
    cfg = _cfg(provider)
    assert cfg.provider == provider
    assert cfg.base_url.startswith("https://")
    assert cfg.model  # a default model exists per provider


def test_unknown_provider_rejected() -> None:
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        provider_config({"LLM_PROVIDER": "mystery", "LLM_API_KEY": "x"})


def test_missing_key_rejected() -> None:
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        provider_config({"LLM_PROVIDER": PROVIDERS[0]})


def test_env_overrides_beat_defaults() -> None:
    cfg = provider_config(
        {
            "LLM_PROVIDER": PROVIDERS[0],
            "LLM_API_KEY": "x",
            "LLM_BASE_URL": "https://proxy.example.com",
            "LLM_MODEL": "custom-model",
        }
    )
    assert cfg.base_url == "https://proxy.example.com"
    assert cfg.model == "custom-model"


# --- wire schema is generated from the pydantic model (7b single source) ---


def test_wire_schema_requires_evidence_quotes() -> None:
    schema = submit_assessment_tool()["function"]["parameters"]
    assert "evidence_quotes" in schema["required"]
    assert schema["properties"]["score"]["minimum"] == 0
    assert schema["properties"]["score"]["maximum"] == 5


def test_model_rejects_stray_fields_and_bad_score() -> None:
    with pytest.raises(Exception):
        SubmitAssessment.model_validate({**VALID_ARGS, "confidence": 0.9})
    with pytest.raises(Exception):
        SubmitAssessment.model_validate({**VALID_ARGS, "score": 6})
    with pytest.raises(Exception):
        SubmitAssessment.model_validate({**VALID_ARGS, "evidence_quotes": []})


# --- the retry/degrade chain (D3-②, decision 3-ii client half) ---


@pytest.mark.parametrize("provider", PROVIDERS)
def test_ok_first_try(provider: str) -> None:
    completer = _completer([json.dumps(VALID_ARGS)])
    call = call_with_validation(
        [{"role": "user", "content": "assess"}],
        SubmitAssessment,
        submit_assessment_tool(),
        completer,
        _cfg(provider),
    )
    assert not call.degraded
    assert call.result is not None and call.result.score == 2
    assert [a.status for a in call.attempts] == ["ok"]
    assert call.attempts[0].provider == provider


@pytest.mark.parametrize("provider", PROVIDERS)
def test_malformed_then_ok_retries_with_corrective_message(provider: str) -> None:
    messages: list[dict[str, Any]] = [{"role": "user", "content": "assess"}]
    completer = _completer(["{not json", json.dumps(VALID_ARGS)])
    call = call_with_validation(
        messages, SubmitAssessment, submit_assessment_tool(), completer, _cfg(provider)
    )
    assert not call.degraded
    assert [a.status for a in call.attempts] == ["malformed_output", "ok"]
    assert [a.attempt for a in call.attempts] == [1, 2]
    corrective = messages[-1]["content"]
    assert "not a valid submit_assessment call" in corrective
    assert "{not json" not in corrective  # field paths / reasons only, never payload text


@pytest.mark.parametrize("provider", PROVIDERS)
def test_double_malformed_degrades_visibly(provider: str) -> None:
    bad = json.dumps({**VALID_ARGS, "score": 99})
    completer = _completer([bad, bad])
    call = call_with_validation(
        [{"role": "user", "content": "assess"}],
        SubmitAssessment,
        submit_assessment_tool(),
        completer,
        _cfg(provider),
    )
    assert call.degraded and call.result is None
    assert [a.status for a in call.attempts] == ["malformed_output", "malformed_output"]
    # metadata survives for trajectory logging even when degraded
    assert all(a.tokens_in == 100 and a.model == _cfg(provider).model for a in call.attempts)


def test_transport_error_counts_as_attempt() -> None:
    def exploding(messages: list[dict[str, Any]], tool_schema: dict[str, Any]) -> RawCompletion:
        raise ConnectionError("boom")

    call = call_with_validation(
        [{"role": "user", "content": "assess"}],
        SubmitAssessment,
        submit_assessment_tool(),
        exploding,
        _cfg(PROVIDERS[0]),
    )
    assert call.degraded
    assert [a.status for a in call.attempts] == ["error", "error"]


def test_validation_reason_names_fields_not_values() -> None:
    messages: list[dict[str, Any]] = [{"role": "user", "content": "assess"}]
    secret_value = "TOP-SECRET-RESUME-SENTENCE-THAT-MUST-NOT-LEAK"
    bad = json.dumps({**VALID_ARGS, "score": secret_value})
    completer = _completer([bad, json.dumps(VALID_ARGS)])
    call_with_validation(
        messages, SubmitAssessment, submit_assessment_tool(), completer, _cfg(PROVIDERS[0])
    )
    assert secret_value not in messages[-1]["content"]
    assert "score" in messages[-1]["content"]  # the field path is named
