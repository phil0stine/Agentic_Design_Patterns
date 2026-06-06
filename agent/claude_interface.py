"""Thin wrapper around the Anthropic SDK with retry logic."""

from __future__ import annotations

import logging
from typing import Any

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-opus-4-8"


class ClaudeInterface:
    """
    Wraps anthropic.Anthropic.messages.create with:
    - Automatic retry on transient network / rate-limit errors
    - Consistent parameter handling
    """

    def __init__(self, config: dict) -> None:
        self.client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
        self.model = config.get("model", _DEFAULT_MODEL)
        self.max_tokens = config.get("max_tokens", 8192)

    @retry(
        retry=retry_if_exception_type(
            (anthropic.APIConnectionError, anthropic.RateLimitError)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def complete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> anthropic.types.Message:
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools
        log.debug("API call | model=%s turns=%d", self.model, len(messages))
        return self.client.messages.create(**kwargs)
