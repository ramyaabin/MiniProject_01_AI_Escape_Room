"""Version 2 game engine: applies validated actions to the game state.

Flow for one turn (see process_turn):
    parsed action -> fill in missing target -> validate_action()
        -> if valid: apply the change to a COPY of the state
        -> return (new_state, result)

`result` is a plain dict that says what happened. It contains a ready-made
text description (`message`) so the game works without Gemini, plus the
facts the LLM narrator is allowed to mention.

Puzzle solutions are read from the room JSON here and in validator.py only.
They are never put into an LLM prompt.
"""

from __future__ import annotations

from version_2.game_state import (
    all_puzzles_solved, copy_state, new_game_state, record_turn,
)
from version_2.validator import USEFUL_COMBINATIONS, validate_action


def restart_game(room: dict) -> dict:
    return new_game_state(room)


def make_result(success: bool, outcome: str, message: str, new_clues=None) -> dict:
    return {
        "success": success,
        "outcome": outcome,          # "ok" or a validator reason such as "wrong_code"
        "message": message,          # deterministic description (fallback narration)
        "new_clues": new_clues or [],
        "escaped": False,
    }


# --- small helpers -----------------------------------------------------------

def _reveal(state: dict, object_ids) -> None:
    for object_id in object_ids:
        if object_id not in state["visible_objects"]:
            state["visible_objects"].append(object_id)


def _add_clues(state: dict, room: dict, clue_ids) -> list[str]:
    """Record new clues and return their text (only the ones not seen before)."""
    new = []
    for clue_id in clue_ids:
        if clue_id not in state["discovered_clues"]:
            state["discovered_clues"].append(clue_id)
            new.append(room["clues"][clue_id])
    return new


def solve_puzzle(state: dict, puzzle_id: str) -> None:
    """Mark a puzzle as solved. Solved puzzles are never set back to False."""
    state["puzzles"][puzzle_id] = True


def _drawer_contents(state: dict, room: dict) -> str:
    remaining = [
        item["name"] for item_id, item in room["items"].items()
        if item["location"] == "drawer" and item_id not in state["taken_items"]
    ]
    if not remaining:
        return "The drawer is empty now."
    return "Inside you see: " + " and ".join(f"a {name}" for name in remaining) + "."


# --- one function per kind of action -------------------------------------------

def look_around(state: dict, room: dict) -> dict:
    extra = [room["objects"][o]["name"] for o in state["visible_objects"]
             if not room["objects"][o].get("visible_at_start")]
    message = room["room_description"]
    if extra:
        message += " You have also noticed: " + ", ".join(extra) + "."
    return make_result(True, "ok", message)


def examine_object(state: dict, room: dict, action: dict) -> dict:
    item_id = action.get("item")
    if item_id and not action.get("target"):
        return make_result(True, "ok", room["items"][item_id]["description"])

    target = action["target"]
    obj = room["objects"][target]
    state["last_target"] = target
    if target not in state["examined_objects"]:
        state["examined_objects"].append(target)
    _reveal(state, obj.get("reveals", []))
    new_clues = _add_clues(state, room, obj.get("clues", []))

    message = obj["description"]
    if target == "drawer" and not state["drawer_locked"]:
        message = f"{obj['description_unlocked']} {_drawer_contents(state, room)}"
    elif target == "painting" and state["painting_unlocked"]:
        message = obj["description_unlocked"]
    elif target == "brass_plate" and state["puzzles"]["tiny_inscription"]:
        message = "Through the magnifying glass you re-read the inscription: " + room["clues"]["plate_inscription"]
    elif target == "door" and all_puzzles_solved(state):
        message += " The keypad now glows faintly, as if it is finally listening."
    return make_result(True, "ok", message, new_clues)


def collect_item(state: dict, room: dict, action: dict) -> dict:
    item_id = action["item"]
    state["inventory"].append(item_id)
    state["taken_items"].append(item_id)
    item = room["items"][item_id]
    return make_result(True, "ok", f"You take the {item['name']}. {item['description']}")


def use_item(state: dict, room: dict, action: dict) -> dict:
    item_id, target = action["item"], action["target"]
    state["last_target"] = target
    puzzle = USEFUL_COMBINATIONS[(item_id, target)]

    if puzzle == "hidden_portrait":
        state["painting_unlocked"] = True
        solve_puzzle(state, "hidden_portrait")
        _reveal(state, ["alcove", "brass_plate"])
        message = (
            "The brass key slides into the tiny keyhole and turns with a soft click. "
            f"{room['objects']['painting']['description_unlocked']} "
            f"{room['objects']['alcove']['description']}"
        )
        return make_result(True, "ok", message)

    # tiny_inscription: reading the plate with the magnifying glass
    first_time = not state["puzzles"]["tiny_inscription"]
    solve_puzzle(state, "tiny_inscription")
    _reveal(state, ["brass_plate"])
    new_clues = _add_clues(state, room, ["plate_inscription"])
    intro = ("You hold the magnifying glass to the brass plate and the tiny letters grow sharp."
             if first_time else "You read the brass plate again through the magnifying glass.")
    return make_result(True, "ok", f"{intro} It says: {room['clues']['plate_inscription'].split(': ', 1)[1]}",
                       new_clues)


def open_object(state: dict, room: dict, action: dict) -> dict:
    """Opening something already unlocked (or a book) is the same as examining it."""
    target = action["target"]
    if target == "painting":
        return examine_object(state, room, {**action, "target": "alcove"})
    return examine_object(state, room, action)


def open_drawer(state: dict, room: dict) -> dict:
    state["drawer_locked"] = False
    solve_puzzle(state, "crimson_volumes")
    message = ("The four wheels click into place and the dial lock springs open. "
               f"{room['objects']['drawer']['description_unlocked']} {_drawer_contents(state, room)}")
    return make_result(True, "ok", message)


def attempt_door_unlock(state: dict, room: dict) -> dict:
    state["door_locked"] = False
    state["escaped"] = True
    result = make_result(True, "ok",
                         "The keypad glows gold. Deep inside the door, heavy bolts slide back one by one. "
                         "The iron-bound door swings open onto cool night air. You have escaped the "
                         "Forgotten Library.")
    result["escaped"] = True
    return result


def enter_code(state: dict, room: dict, action: dict) -> dict:
    state["last_target"] = action["target"]
    if action["target"] == "drawer":
        return open_drawer(state, room)
    return attempt_door_unlock(state, room)


def show_inventory(state: dict, room: dict) -> dict:
    if not state["inventory"]:
        return make_result(True, "ok", "You are not carrying anything yet.")
    names = [room["items"][i]["name"] for i in state["inventory"]]
    return make_result(True, "ok", "You are carrying: " + ", ".join(names) + ".")


def give_hint(state: dict, room: dict) -> dict:
    """A deterministic next-step hint based on progress. It points the way without giving codes."""
    examined, visible = state["examined_objects"], state["visible_objects"]
    if "desk" not in examined:
        hint = "The study desk in the middle of the room looks well used. Start there."
    elif "journal" not in examined:
        hint = "Read the leather journal lying on the desk."
    elif "crimson_books" not in visible:
        hint = "The journal talks about crimson volumes. Where would you keep books?"
    elif "crimson_books" not in examined:
        hint = "Take a closer look at the four crimson volumes on the bookshelf."
    elif state["drawer_locked"]:
        hint = ("Each crimson volume holds one digit. The journal says to read them in the order "
                "they were written, so begin with Volume I. Try those four digits on the drawer.")
    elif len(state["taken_items"]) < len(room["items"]):
        hint = "The drawer is open. Take what Thorne left inside."
    elif "painting" not in examined:
        hint = "Study the portrait on the east wall, including its frame."
    elif not state["painting_unlocked"]:
        hint = "That tiny keyhole in the portrait frame could fit something you are carrying."
    elif not state["puzzles"]["tiny_inscription"]:
        hint = "The writing on the brass plate is too small to read. Something you carry could help."
    else:
        hint = ("Combine what the brass plate tells you with the year painted on the portrait, "
                "then try it on the exit door.")
    return make_result(True, "ok", hint)


# --- target inference + the main entry point -----------------------------------

def _infer_target(state: dict, action: dict) -> dict:
    """Fill in an obvious missing target, e.g. 'enter 1234' or 'use the key'."""
    action = dict(action)
    if action["verb"] == "enter_code" and not action.get("target"):
        if state["last_target"] in ("drawer", "door"):
            action["target"] = state["last_target"]
        else:
            action["target"] = "drawer" if state["drawer_locked"] else "door"
    if action["verb"] == "use" and action.get("item") and not action.get("target"):
        if state["last_target"]:
            action["target"] = state["last_target"]
    if action["verb"] == "use" and action.get("target") == "alcove" and action.get("item") == "brass_key":
        action["target"] = "painting"
    return action


HANDLERS = {
    "look": lambda s, r, a: look_around(s, r),
    "examine": examine_object,
    "take": collect_item,
    "use": use_item,
    "open": open_object,
    "enter_code": enter_code,
    "inventory": lambda s, r, a: show_inventory(s, r),
    "hint": lambda s, r, a: give_hint(s, r),
}


def process_turn(state: dict, room: dict, action: dict) -> tuple[dict, dict]:
    """Validate and apply one action. Returns (new_state, result).

    The input state is never modified. If validation fails, the only change in
    the returned state is the turn counter, the history record and (for wrong
    codes) the failed-attempt counter.
    """
    new_state = copy_state(state)
    new_state["turn"] += 1
    action = _infer_target(new_state, action)

    verdict = validate_action(new_state, room, action)
    if verdict["ok"]:
        result = HANDLERS[action["verb"]](new_state, room, action)
    else:
        result = make_result(False, verdict["reason"], verdict["message"])
        if verdict["reason"] == "wrong_code":
            new_state["failed_attempts"][action["target"]] += 1

    result["action"] = action
    record_turn(new_state, action.get("raw", ""), action, result["success"], result["outcome"])
    return new_state, result
