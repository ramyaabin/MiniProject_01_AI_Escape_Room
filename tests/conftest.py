"""Shared pytest setup: import paths and a fake LLM so tests never call the real API."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Tests must be repeatable and free: never use a real key from .env.
os.environ["GEMINI_API_KEY"] = ""

import pytest  # noqa: E402

from common.llm_client import LLMError  # noqa: E402
from common.room_data import load_room  # noqa: E402


class FakeLLM:
    """Stands in for GeminiClient. Returns scripted replies and records every call."""

    def __init__(self, replies=None, error: str | None = None, configured: bool = True):
        self.replies = list(replies or [])
        self.error = error
        self.is_configured = configured
        self.model = "fake-model"
        self.calls = []

    def generate(self, system_prompt, turns, **kwargs):
        self.calls.append({"system_prompt": system_prompt, "turns": turns, **kwargs})
        if self.error:
            raise LLMError(self.error)
        if not self.replies:
            return "The Game Master nods silently."
        return self.replies.pop(0)


@pytest.fixture
def room():
    return load_room()
