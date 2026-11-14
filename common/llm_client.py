"""Shared wrapper around the Google Gemini API.

Both versions of the game talk to Gemini through this one class so that the
API key handling, timeouts and error messages are written only once.

The rest of the code never imports the Gemini SDK directly. It only calls
GeminiClient.generate(), which either returns text or raises LLMError with a
message that is safe to show to the player.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# gemini-3.5-flash-lite is a stable model on the free tier (checked Nov 2026).
# It can be changed in .env without touching the code.
DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 30.0
PLACEHOLDER_KEYS = {"", "your-gemini-api-key-here"}


class LLMError(Exception):
    """The LLM could not give a usable answer. str(error) is player-friendly."""


class GeminiClient:
    """Small helper that sends a system prompt plus a conversation to Gemini."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout_seconds: float | None = None):
        key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.api_key = key.strip()
        self.model = model or os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_MODEL
        if timeout_seconds is None:
            try:
                timeout_seconds = float(os.getenv("GEMINI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
            except ValueError:
                timeout_seconds = DEFAULT_TIMEOUT_SECONDS
        self.timeout_seconds = timeout_seconds
        self._sdk_client = None  # created lazily on the first request

    @property
    def is_configured(self) -> bool:
        return self.api_key not in PLACEHOLDER_KEYS

    def _client(self):
        if not self.is_configured:
            raise LLMError(
                "No Gemini API key found. Copy .env.example to .env and set GEMINI_API_KEY."
            )
        if self._sdk_client is None:
            from google import genai
            from google.genai import types

            self._sdk_client = genai.Client(
                api_key=self.api_key,
                # The SDK expects the timeout in milliseconds.
                http_options=types.HttpOptions(timeout=int(self.timeout_seconds * 1000)),
            )
        return self._sdk_client

    def generate(self, system_prompt: str, turns: list[dict], temperature: float = 0.8,
                 json_schema: dict | None = None, max_output_tokens: int = 1024) -> str:
        """Send the conversation and return the model's reply text.

        turns: list of {"role": "user" | "model", "text": "..."} in order.
        json_schema: if given, Gemini is asked to answer with JSON matching it.
        """
        from google.genai import errors, types

        client = self._client()
        contents = [
            types.Content(role=turn["role"], parts=[types.Part(text=turn["text"])])
            for turn in turns
        ]
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        if json_schema is not None:
            config.response_mime_type = "application/json"
            config.response_json_schema = json_schema

        try:
            response = client.models.generate_content(
                model=self.model, contents=contents, config=config
            )
        except errors.ClientError as exc:
            raise LLMError(_client_error_message(exc, self.model)) from exc
        except errors.ServerError as exc:
            raise LLMError("The Gemini service is temporarily unavailable. Please try again.") from exc
        except Exception as exc:  # network problems, timeouts, unexpected SDK errors
            if "timeout" in type(exc).__name__.lower() or "timed out" in str(exc).lower():
                raise LLMError(
                    f"Gemini did not answer within {self.timeout_seconds:.0f} seconds."
                ) from exc
            raise LLMError(f"Could not reach Gemini ({type(exc).__name__}).") from exc

        try:
            text = (response.text or "").strip()
        except Exception:  # the SDK can fail to read text from blocked/odd responses
            text = ""
        if not text:
            raise LLMError("The Game Master returned an empty response.")
        return text


def _client_error_message(exc, model: str) -> str:
    """Turn a 4xx error from the API into a message the player can act on."""
    code = getattr(exc, "code", None)
    detail = str(exc).lower()
    if code in (401, 403) or "api key" in detail or "api_key" in detail:
        return "The Gemini API key was rejected. Check GEMINI_API_KEY in your .env file."
    if code == 404:
        return f"The model '{model}' is not available. Set GEMINI_MODEL in .env to a current model."
    if code == 429:
        return "Gemini free-tier rate limit reached. Wait a minute and try again."
    return f"Gemini rejected the request (error {code})."
