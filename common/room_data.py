"""Loads the room definition (story, objects, clues, solutions) from JSON."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

ROOM_FILE = Path(__file__).resolve().parent.parent / "game_data" / "forgotten_library.json"


@lru_cache(maxsize=None)
def _read_room_file(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_room(path: Path | str = ROOM_FILE) -> dict:
    """Return a fresh copy of the room so callers can never edit the cached original."""
    return copy.deepcopy(_read_room_file(str(path)))
