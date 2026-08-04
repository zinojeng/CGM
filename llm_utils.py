"""Utility helpers for invoking OpenAI models with resilient fallbacks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple

from openai import OpenAI


RESPONSES_PREFIXES: Tuple[str, ...] = ("o", "gpt-5", "gpt-4.1", "gpt-4o")
REASONING_PREFIXES: Tuple[str, ...] = ("o",)
# 主模型失敗時的備援順序：先退到同世代較便宜的 GPT-5.6，最後才退到 GPT-4o mini。
# 舊的 gpt-5-mini 將於 2026-12-11 自 API 下線，已改為 gpt-5.6-terra / luna。
DEFAULT_FALLBACK_MODELS: List[str] = ["gpt-5.6-terra", "gpt-5.6-luna", "gpt-4o-mini"]


def _resolve_max_output_tokens(model_name: str, requested: int) -> int:
    lower = model_name.lower()
    if lower.startswith("gpt-5"):
        return max(requested, 4096)
    return requested


def _uses_responses_api(model_name: str) -> bool:
    lower = model_name.lower()
    return any(lower.startswith(prefix) for prefix in RESPONSES_PREFIXES)




def _supports_temperature_parameter(model_name: str) -> bool:
    lower = model_name.lower()
    if lower.startswith("gpt-5"):
        return False
    return True



def _supports_reasoning_effort(model_name: str) -> bool:
    lower = model_name.lower()
    return any(lower.startswith(prefix) for prefix in REASONING_PREFIXES)


def _messages_to_responses_input(messages: Sequence[dict]) -> List[dict]:
    """Convert chat messages into Responses API input format."""

    formatted: List[dict] = []

    for message in messages:
        role = (message or {}).get("role") or "user"
        raw_content = (message or {}).get("content", "")
        content_blocks: List[dict] = []

        def _normalize_block_type(block_type: str | None) -> str:
            allowed = {"input_text", "input_image", "output_text", "refusal", "input_file", "computer_screenshot", "summary_text"}
            if not block_type:
                return "input_text" if role != "assistant" else "output_text"
            lowered = str(block_type).lower()
            if lowered == "text":
                return "input_text" if role != "assistant" else "output_text"
            if lowered in allowed:
                return lowered
            return "input_text" if role != "assistant" else "output_text"

        def _append_text_block(text_value, *, block_type: str | None = None) -> None:
            if text_value is None:
                return
            text_str = str(text_value).strip()
            if not text_str:
                return
            normalized_type = _normalize_block_type(block_type)
            content_blocks.append({"type": normalized_type, "text": text_str})

        if isinstance(raw_content, list):
            for item in raw_content:
                if isinstance(item, dict):
                    block_type = item.get("type")
                    text_payload = item.get("text")
                    if isinstance(text_payload, dict):
                        text_payload = text_payload.get("value") or text_payload.get("text")
                    if text_payload is None and "content" in item:
                        nested = item.get("content")
                        if isinstance(nested, (list, tuple)):
                            for nested_item in nested:
                                if isinstance(nested_item, dict):
                                    nested_text = nested_item.get("text")
                                    if isinstance(nested_text, dict):
                                        nested_text = nested_text.get("value") or nested_text.get("text")
                                    if nested_text:
                                        _append_text_block(nested_text, block_type=block_type)
                                elif isinstance(nested_item, str):
                                    _append_text_block(nested_item, block_type=block_type)
                        elif isinstance(nested, str):
                            _append_text_block(nested, block_type=block_type)
                        continue
                    _append_text_block(text_payload, block_type=block_type)
                elif isinstance(item, str):
                    _append_text_block(item)
        else:
            _append_text_block(raw_content)

        if not content_blocks:
            continue

        formatted.append({"role": role, "content": content_blocks})

    return formatted



def _should_try_fallback(error_message: str) -> bool:
    lowered = (error_message or "").lower()
    if "empty_response_text" in lowered:
        return True
    keywords = [
        "model",
        "not",
        "exist",
        "access",
        "permission",
        "model_not_found",
        "unsupported_parameter",
        "rate limit",
    ]
    return all(keyword in lowered for keyword in ["model", "not"]) or any(keyword in lowered for keyword in keywords)


def _extract_text_from_response(response) -> str:
    text = (getattr(response, "output_text", None) or "").strip()
    if text:
        return text

    collected: List[str] = []
    seen: set[int] = set()

    def _collect(value) -> None:
        if value is None:
            return
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                collected.append(stripped)
            return
        marker = id(value) if isinstance(value, (list, tuple, dict)) or hasattr(value, "__dict__") else None
        if marker is not None:
            if marker in seen:
                return
            seen.add(marker)
        if isinstance(value, (list, tuple)):
            for item in value:
                _collect(item)
            return
        if isinstance(value, dict):
            for key in ("text", "output_text", "value", "data"):
                if key in value:
                    _collect(value[key])
            for key in ("content", "parts", "messages", "annotations"):
                if key in value:
                    _collect(value[key])
            return
        if hasattr(value, "text"):
            _collect(getattr(value, "text"))
        if hasattr(value, "output_text"):
            _collect(getattr(value, "output_text"))
        if hasattr(value, "value"):
            _collect(getattr(value, "value"))
        if hasattr(value, "content"):
            _collect(getattr(value, "content"))
        if hasattr(value, "annotations"):
            _collect(getattr(value, "annotations"))
        data = getattr(value, "__dict__", None)
        if isinstance(data, dict):
            _collect(data)

    _collect(getattr(response, "output", None))
    if not collected:
        _collect(getattr(response, "data", None))
    if not collected and hasattr(response, "model_dump"):
        try:
            _collect(response.model_dump())
        except Exception:  # pylint: disable=broad-except
            pass

    return "\n".join(collected).strip()


@dataclass
class LLMCallResult:
    text: str
    model_used: str
    failures: List[Tuple[str, str]]


def call_with_fallback(
    api_key: str,
    primary_model: str,
    messages: Sequence[dict],
    *,
    max_tokens: int,
    temperature: float = 0.2,
    fallback_models: Iterable[str] | None = None,
) -> LLMCallResult:
    """Call an OpenAI model and fall back to alternatives when needed."""

    client = OpenAI(api_key=api_key)

    tried_failures: List[Tuple[str, str]] = []
    primary_lower = primary_model.lower()
    models_to_try: List[str] = [primary_model]

    if fallback_models:
        for candidate in fallback_models:
            if candidate and candidate.lower() not in {m.lower() for m in models_to_try}:
                models_to_try.append(candidate)

    for idx, model_name in enumerate(models_to_try):
        try:
            text = _call_single_model(
                client,
                model_name=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return LLMCallResult(text=text, model_used=model_name, failures=tried_failures)
        except Exception as exc:  # pylint: disable=broad-except
            error_message = str(exc)
            tried_failures.append((model_name, error_message))
            is_last_candidate = idx == len(models_to_try) - 1
            if is_last_candidate or not _should_try_fallback(error_message):
                aggregated = \
                    "; ".join(f"{model} failed: {msg}" for model, msg in tried_failures)
                raise RuntimeError(aggregated) from exc

    # Control should never reach here because the loop either returns or raises.
    raise RuntimeError("No models were attempted for the request.")


def request_llm_text(
    api_key: str | None,
    *,
    primary_model: str,
    messages: Sequence[dict],
    max_tokens: int,
    temperature: float = 0.2,
    fallback_models: Iterable[str] | None = None,
    missing_key_error: str | None = None,
    error_formatter: Callable[[str, Exception], str] | None = None,
    fallback_notice_formatter: Callable[[str, LLMCallResult], str] | None = None,
) -> Tuple[str | None, str | None, LLMCallResult | None, str | None]:
    """Wrapper around ``call_with_fallback`` that returns structured success/error feedback."""

    if not api_key:
        return None, missing_key_error or "Missing API key for LLM call.", None, None

    def _default_error_formatter(model_name: str, exc: Exception) -> str:
        return f"LLM call failed ({model_name}): {exc}"

    formatter = error_formatter or _default_error_formatter

    try:
        result = call_with_fallback(
            api_key,
            primary_model=primary_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            fallback_models=fallback_models,
        )
    except RuntimeError as error:
        return None, formatter(primary_model, error), None, None
    except Exception as error:  # pylint: disable=broad-except
        return None, formatter(primary_model, error), None, None

    text = result.text or ""
    notice = None
    if (
        fallback_notice_formatter
        and result.failures
        and result.model_used
        and result.model_used.lower() != primary_model.lower()
    ):
        notice = fallback_notice_formatter(primary_model, result)

    return text, None, result, notice


def _call_single_model(
    client: OpenAI,
    *,
    model_name: str,
    messages: Sequence[dict],
    max_tokens: int,
    temperature: float,
) -> str:
    if _uses_responses_api(model_name):
        kwargs = {
            "model": model_name,
            "input": _messages_to_responses_input(messages),
            "max_output_tokens": _resolve_max_output_tokens(model_name, max_tokens),
        }
        if temperature is not None and _supports_temperature_parameter(model_name):
            kwargs["temperature"] = temperature
        if _supports_reasoning_effort(model_name):
            kwargs["reasoning"] = {"effort": "medium"}

        response = client.responses.create(**kwargs)
        text = _extract_text_from_response(response)
        if not text:
            raw_payload = ""
            try:
                if hasattr(response, "model_dump"):
                    raw_payload = response.model_dump()
                elif hasattr(response, "to_dict"):
                    raw_payload = response.to_dict()
                else:
                    raw_payload = getattr(response, "__dict__", response)
            except Exception:  # pylint: disable=broad-except
                raw_payload = response
            snippet = str(raw_payload)
            if len(snippet) > 2000:
                snippet = snippet[:2000] + "..."
            raise ValueError(f"empty_response_text (payload_snippet={snippet})")
        return text

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        n=1,
    )
    if not completion.choices:
        raise ValueError("empty_chat_completion")
    message = completion.choices[0].message
    return (getattr(message, "content", None) or "").strip()
