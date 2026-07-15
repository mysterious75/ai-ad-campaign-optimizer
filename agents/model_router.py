"""
ModelRouter: routes LLM calls across multiple models/providers.

Reads model list from env, rotates round-robin, falls back on failure.
Supports Anthropic (Claude) and Google (Gemini) APIs.

Env config:
  LLM_MODELS="gemini-2.5-flash,gemini-2.5-pro,gemini-3.5-flash,claude-sonnet-4-20250514"
  GEMINI_API_KEY="..."
  ANTHROPIC_API_KEY="..."
"""

import json
import logging
import os
import itertools
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ModelRouter:
    def __init__(self):
        self.models = self._load_models()
        self._iterator = itertools.cycle(self.models) if self.models else None
        self._fallback_order = list(self.models)
        self.usage = {m: {"calls": 0, "failures": 0, "tokens": 0} for m in self.models}

    def _load_models(self) -> list[str]:
        raw = os.getenv("LLM_MODELS", "")
        if not raw:
            default = os.getenv("ANTHROPIC_API_KEY") and "claude-sonnet-4-20250514" or ""
            if os.getenv("GEMINI_API_KEY"):
                default = "gemini-2.5-flash"
            return [default] if default else []
        return [m.strip() for m in raw.split(",") if m.strip()]

    def get_next(self) -> Optional[str]:
        if not self._iterator:
            return None
        return next(self._iterator)

    def call(self, system_prompt: str, user_message: str, max_tokens: int = 2000) -> str:
        if not self.models:
            raise RuntimeError("No LLM models configured. Set LLM_MODELS, GEMINI_API_KEY, or ANTHROPIC_API_KEY in .env")

        errors = []
        for model in self._fallback_order:
            try:
                result = self._call_model(model, system_prompt, user_message, max_tokens)
                self.usage[model]["calls"] += 1
                logger.info(f"LLM call succeeded on {model}")
                return result
            except Exception as e:
                self.usage[model]["failures"] += 1
                logger.warning(f"Model {model} failed: {e}")
                errors.append(f"{model}: {e}")

                next_model = self.get_next()
                if next_model and next_model not in self._fallback_order:
                    self._fallback_order.append(next_model)

        raise RuntimeError(f"All {len(self.models)} models failed: {'; '.join(errors)}")

    def _call_model(self, model: str, system: str, user_msg: str, max_tokens: int) -> str:
        claude_models = {"claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"}
        gemini_prefixes = ("gemini-", "gemma-")

        if model in claude_models or model.startswith("claude"):
            return self._call_anthropic(model, system, user_msg, max_tokens)
        elif model.startswith(gemini_prefixes):
            return self._call_gemini(model, system, user_msg, max_tokens)
        else:
            raise ValueError(f"Unknown model provider for: {model}")

    def _call_anthropic(self, model: str, system: str, user_msg: str, max_tokens: int) -> str:
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        content = response.content[0].text
        self.usage[model]["tokens"] += response.usage.input_tokens + response.usage.output_tokens
        return content

    def _call_gemini(self, model: str, system: str, user_msg: str, max_tokens: int) -> str:
        import httpx

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")

        payload = {
            "contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user_msg}"}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.1,
            },
        }

        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}",
            json=payload,
            timeout=45,
        )

        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 5))
            logger.warning(f"Gemini rate limited on {model}, retry after {retry_after}s")
            time.sleep(retry_after)

            response = httpx.post(
                f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}",
                json=payload,
                timeout=45,
            )

        if response.status_code == 429:
            raise RuntimeError(f"Gemini rate limited on {model} after retry")

        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates for {model}")

        text = ""
        for part in candidates[0].get("content", {}).get("parts", []):
            text += part.get("text", "")

        if not text:
            finish = candidates[0].get("finishReason", "unknown")
            raise RuntimeError(f"Gemini empty response (finish: {finish}) for {model}")

        usage = data.get("usageMetadata", {})
        if usage:
            pt = usage.get("promptTokenCount", 0)
            gt = usage.get("candidatesTokenCount", 0)
            self.usage[model]["tokens"] += pt + gt

        return text

    def get_usage_report(self) -> str:
        lines = []
        for model, data in self.usage.items():
            lines.append(f"  {model}: {data['calls']} calls, {data['failures']} failures, ~{data['tokens']} tokens")
        return "\n".join(lines)
