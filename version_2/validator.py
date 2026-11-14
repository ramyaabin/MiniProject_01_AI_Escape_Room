"""Version 2 action validation: the game rules, written as plain Python checks.

Every function here only READS the state and returns a verdict:
    {"ok": True,  "reason": "ok",          "message": ""}
    {"ok": False, "reason": "wrong_code",  "message": "The dial will not turn..."}

Nothing in this file changes the state, and nothing here asks the LLM.
That is the key difference from Version 1: whether an action succeeds is
decided by deterministic code, so it cannot be argued with or forgotten.
"""

from __future__ import annotations

from version_2.game_state import all_puzzles_solved

CODE_LENGTH = 4
CODE_TARGETS = ("drawer", "door")

# The only item/target pairs that do something.
USEFUL_COMBINATIONS = {
    ("brass_key", "painting"): "hidden_portrait",
    ("magnifying_glass", "brass_plate"): "tiny_inscription",
    ("magnifying_glass", "alcove"): "tiny_inscription",
}


def ok() -> dict:
    return {"ok": True, "reason": "ok", "message": ""}


def fail(reason: str, message: str) -> dict:
    return {"ok": False, "reason": reason, "message": message}


def _name(room: dict, ident: str) -> str:
    if ident in room["objects"]:
        return room["objects"][ident]["name"]
    return room["items"][ident]["name"]


def is_visible(state: dict, object_id: str) -> bool:
    return object_id in state["visible_objects"]


def item_reachable(state: dict, room: dict, item_id: str) -> bool:
    """An item can be seen if the player carries it or it lies in the open drawer."""
    if item_id in state["inventory"]:
        return True
    in_open_drawer = room["items"][item_id]["location"] == "drawer" and not state["drawer_locked"]
    return in_open_drawer and item_id not in state["taken_items"]


def _no_such_thing(action: dict) -> dict:
    name = action.get("unknown_name")
    if name:
        return fail("no_such_object", f"There is no '{name}' in this room.")
    return fail("no_target", "What exactly do you want to do that with?")


def validate_examine(state, room, action) -> dict:
    target, item = action.get("target"), action.get("item")
    if target:
        if not is_visible(state, target):
            return fail("not_visible", "You don't see anything like that yet.")
        return ok()
    if item:
        if not item_reachable(state, room, item):
            return fail("not_visible", f"You haven't found a {_name(room, item)}.")
        return ok()
    return _no_such_thing(action)


def validate_take(state, room, action) -> dict:
    item, target = action.get("item"), action.get("target")
    if not item:
        if target:
            return fail("not_portable", f"The {_name(room, target)} cannot be carried.")
        return _no_such_thing(action)
    if item in state["inventory"]:
        return fail("already_have", f"You already have the {_name(room, item)}.")
    if not item_reachable(state, room, item):
        return fail("not_visible", f"You haven't found a {_name(room, item)}.")
    return ok()


def validate_use(state, room, action) -> dict:
    item, target = action.get("item"), action.get("target")
    if not item:
        name = action.get("unknown_name")
        if name:
            return fail("no_such_item", f"You don't have a '{name}'.")
        return fail("no_item", "What do you want to use?")
    if item not in state["inventory"]:
        # Inventory rule: you can only use what you have actually collected.
        return fail("not_in_inventory", f"You don't have the {_name(room, item)}.")
    if not target:
        return fail("no_target", f"What do you want to use the {_name(room, item)} on?")
    if not is_visible(state, target):
        return fail("not_visible", "You don't see anything like that yet.")
    puzzle = USEFUL_COMBINATIONS.get((item, target))
    if puzzle is None:
        return fail("no_effect",
                    f"You try the {_name(room, item)} on the {_name(room, target)}, but nothing happens.")
    if puzzle == "hidden_portrait" and state["painting_unlocked"]:
        return fail("already_done", "The portrait is already unlocked and hangs open.")
    return ok()


def validate_open(state, room, action) -> dict:
    target = action.get("target")
    if not target:
        return _no_such_thing(action)
    if not is_visible(state, target):
        return fail("not_visible", "You don't see anything like that yet.")
    if target == "drawer" and state["drawer_locked"]:
        return fail("locked_needs_code",
                    "The drawer will not budge. Its brass dial lock needs a four-digit code.")
    if target == "painting" and not state["painting_unlocked"]:
        return fail("locked_needs_item",
                    "The frame is fixed firmly to the wall. The tiny keyhole at its base suggests it needs a key.")
    if target == "door":
        return fail("locked_needs_code", "The door is locked. The keypad beside it needs a four-digit code.")
    if target in ("drawer", "painting", "journal", "crimson_books", "alcove"):
        return ok()
    return fail("cannot_open", f"The {_name(room, target)} is not something you can open.")


def validate_code(state, room, action) -> dict:
    target, code = action.get("target"), action.get("code")
    if target not in CODE_TARGETS:
        return fail("no_keypad", "Only the desk drawer and the exit door have number locks.")
    if not is_visible(state, target):
        return fail("not_visible", "You don't see anything like that yet.")
    if not code or not code.isdigit() or len(code) != CODE_LENGTH:
        return fail("bad_format", "The lock has exactly four number wheels. Enter four digits.")

    solutions = room["solutions"]
    if target == "drawer":
        if not state["drawer_locked"]:
            return fail("already_done", "The drawer is already unlocked.")
        if code != solutions["drawer_code"]:
            return fail("wrong_code", f"You set the dial to {code} and pull. The drawer stays locked.")
        return ok()

    # The exit door only accepts a code once all three trials are complete,
    # so a guessed or leaked code cannot skip the puzzles.
    if not all_puzzles_solved(state):
        return fail("trials_incomplete",
                    "You key in the digits, but the keypad stays dark and silent. "
                    "The engraving above it reads: 'Only one who has walked my three trials may leave.'")
    if code != solutions["door_code"]:
        return fail("wrong_code", f"You enter {code}. The keypad flashes red and the lock holds.")
    return ok()


VALIDATORS = {
    "examine": validate_examine,
    "take": validate_take,
    "use": validate_use,
    "open": validate_open,
    "enter_code": validate_code,
}


def validate_action(state: dict, room: dict, action: dict) -> dict:
    """Decide whether an action is allowed in the current state."""
    if state["escaped"]:
        return fail("game_over", "You have already escaped. Use Restart to play again.")
    verb = action.get("verb")
    if verb in ("look", "inventory", "hint"):
        return ok()
    if verb == "claim":
        return fail("rule_bypass",
                    "The library does not answer to claims or commands, only to what you actually do. "
                    "Nothing has changed.")
    validator = VALIDATORS.get(verb)
    if validator is None:
        return fail("not_understood",
                    "I'm not sure what you want to do. Try 'examine the desk', 'take the key', "
                    "'use the key on the painting', 'enter 1234 on the drawer' or 'hint'.")
    return validator(state, room, action)
