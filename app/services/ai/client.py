"""Anthropic API client factory.

The client resolves credentials from ANTHROPIC_API_KEY. Routes must gate on
``app.config.ai_enabled()`` before calling ``get_client()`` so construction
never happens without a key.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any

import anthropic
from fastapi import HTTPException, status


class AIResponseError(RuntimeError):
    """The model responded, but not with usable structured output."""


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def call_ai(func: Callable[..., dict[str, Any]], *args: Any) -> dict[str, Any]:
    """Run an AI service function, mapping SDK/response failures to HTTP responses.

    Shared by every route that calls into the Anthropic API, so a rate limit,
    connectivity failure, upstream error, or model refusal always surfaces the
    same way regardless of which feature triggered it.
    """
    try:
        return func(*args)
    except AIResponseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except anthropic.RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Anthropic API rate limit reached — try again shortly.",
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the Anthropic API.",
        ) from exc
    except anthropic.APIStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Anthropic API error: {exc.message}",
        ) from exc
