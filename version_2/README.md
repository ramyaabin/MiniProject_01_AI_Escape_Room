# Version 2 - Reliable AI Escape Room

Python runs the game and Gemini tells the story. Every action is parsed into a structured
command, validated against the game rules and only then applied to the game state.
Gemini describes the result but never changes the state.

## Run it

```powershell
# from the project folder, with the virtual environment active
streamlit run version_2/app.py
```

With a Gemini key in `.env`, the narration comes from Gemini. Without one, the game is still
fully playable using the built-in descriptions from the room JSON.

## Files

| File | Purpose | Key functions |
|---|---|---|
| `game_state.py` | The game state as a plain dict, plus helpers. | `new_game_state`, `public_view`, `record_turn` |
| `action_parser.py` | Turns a sentence into `{verb, item, target, code}`. Rules first, Gemini JSON fallback. | `parse_action`, `parse_with_rules`, `parse_with_llm` |
| `validator.py` | The game rules. Read-only checks that return ok or a reason. | `validate_action`, `validate_use`, `validate_code` |
| `game_engine.py` | Applies valid actions to a copy of the state and builds the result. | `process_turn`, `examine_object`, `collect_item`, `use_item`, `open_drawer`, `attempt_door_unlock`, `solve_puzzle`, `restart_game`, `give_hint` |
| `game_master.py` | Asks Gemini to narrate the result, then checks the narration. | `GameMasterV2.narrate`, `check_narration` |
| `app.py` | Streamlit page with chat, live status, trials, inventory, clues and engine view. | `handle_player_message` |

## One turn

```
sentence -> parse_action() -> process_turn() -> validate_action() -> engine function
         -> new state + result -> GameMasterV2.narrate() -> check_narration() -> screen
```

## Rules enforced in Python

- Objects must exist and must have been discovered (hidden objects appear only after examining their parent).
- Items can only be used if they are in the inventory, and can only be taken once.
- The drawer opens only with its exact four-digit code. Wrong codes are counted.
- The exit door accepts a code only after all three trials are solved, so even the correct
  code cannot skip the puzzles.
- Solved puzzles can never become unsolved, and nothing works after the escape.
- Claims, "admin" commands and requests for answers are refused and change nothing.

## Behaviour when Gemini is unavailable

Missing key, invalid key, rate limit, timeout, server error or an unusable reply: the engine's
own text is shown, and a caption under each message says which narration was used.
