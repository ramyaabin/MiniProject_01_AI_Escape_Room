"""Version 2 game state: one plain Python dictionary that is the single source of truth.

The state is a dict (not a class) so it is easy to print, save as JSON,
compare in tests and show in the UI. Only game_engine.py changes it, and it
always works on a copy so a failed action can never leave half-applied changes.
"""

from __future__ import annotations

import copy
import json

PUZZLE_IDS = ("crimson_volumes", "hidden_portrait", "tiny_inscription")


def new_game_state(room: dict) -> dict:
    """Build the starting state for the room definition loaded from JSON."""
    visible = [obj_id for obj_id, obj in room["objects"].items() if obj.get("visible_at_start")]
    return {
        "room": "forgotten_library",
        "turn": 0,
        "visible_objects": visible,       # objects the player has noticed so far
        "examined_objects": [],           # objects the player has looked at
        "inventory": [],                  # item ids the player carries
        "taken_items": [],                # items removed from the room (cannot be taken twice)
        "discovered_clues": [],           # clue ids, in the order they were found
        "puzzles": {puzzle_id: False for puzzle_id in PUZZLE_IDS},
        "drawer_locked": True,
        "painting_unlocked": False,
        "door_locked": True,
        "escaped": False,
        "failed_attempts": {"drawer": 0, "door": 0},
        "last_target": None,              # last object the player interacted with
        "history": [],                    # one short record per turn
    }


def copy_state(state: dict) -> dict:
    return copy.deepcopy(state)


def puzzles_solved(state: dict) -> int:
    return sum(1 for solved in state["puzzles"].values() if solved)


def all_puzzles_solved(state: dict) -> bool:
    return all(state["puzzles"].values())


def record_turn(state: dict, player_input: str, action: dict, success: bool, outcome: str) -> None:
    """Append a short, structured record of what happened this turn."""
    state["history"].append(
        {
            "turn": state["turn"],
            "input": player_input[:200],
            "action": action.get("verb"),
            "target": action.get("target") or action.get("item"),
            "success": success,
            "outcome": outcome,
        }
    )


def public_view(state: dict, room: dict) -> dict:
    """The part of the state that the LLM narrator is allowed to see.

    It contains names and discovered clues only, never codes or solutions.
    """
    objects, items, clues = room["objects"], room["items"], room["clues"]
    return {
        "visible_objects": [objects[o]["name"] for o in state["visible_objects"]],
        "inventory": [items[i]["name"] for i in state["inventory"]],
        "discovered_clues": [clues[c] for c in state["discovered_clues"]],
        "puzzles_solved": [room["puzzles"][p]["title"] for p, done in state["puzzles"].items() if done],
        "drawer": "locked" if state["drawer_locked"] else "open",
        "door": "locked" if state["door_locked"] else "open",
        "escaped": state["escaped"],
    }


SCENE_AREAS = {
    "bookshelf": "bookshelf", "crimson_books": "bookshelf",
    "desk": "desk", "journal": "desk", "drawer": "desk", "lamp": "desk",
    "painting": "painting", "alcove": "painting", "brass_plate": "painting",
    "door": "door",
}


def scene_view(state: dict, room: dict) -> dict:
    """Flags for the room illustration (common/room_scene.py), taken only from the state."""
    drawer_open = not state["drawer_locked"]
    items_in_drawer = [
        item_id for item_id, item in room["items"].items()
        if item["location"] == "drawer" and item_id not in state["taken_items"]
    ]
    return {
        "crimson_found": "crimson_books" in state["visible_objects"],
        "drawer_open": drawer_open,
        "drawer_items": items_in_drawer if drawer_open else [],
        "painting_open": state["painting_unlocked"],
        "plate_read": state["puzzles"]["tiny_inscription"],
        "keypad_active": all_puzzles_solved(state),
        "door_open": state["escaped"],
        "highlight": SCENE_AREAS.get(state["last_target"]),
    }


def to_json(state: dict) -> str:
    return json.dumps(state, indent=2)
