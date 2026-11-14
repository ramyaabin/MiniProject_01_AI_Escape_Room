# Version 1 - Interactive AI Escape Room

The baseline version. Gemini acts as the Game Master and runs the entire game through
one system prompt and the conversation history.

## Run it

```powershell
# from the project folder, with the virtual environment active
streamlit run version_1/app.py
```

A Gemini API key in `.env` is required. Without it the page explains how to add one, and
the chat input is disabled.

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit page: introduction, instructions, chat, status panel, restart button, victory screen. |
| `game_master.py` | Builds the system prompt from `game_data/forgotten_library.json` and sends the chat history to Gemini. |

Shared code: `common/llm_client.py` (Gemini calls and error handling), `common/theme.py` (styling).

## How it works

1. `build_system_prompt()` writes the story, all objects, items, puzzles **and their solutions**
   into one prompt and tells Gemini how to behave as the Game Master.
2. Each turn, `GameMasterV1.respond()` sends that prompt plus the whole conversation to Gemini.
3. Gemini decides what happens. When it believes the player has escaped it writes `[ESCAPED]`,
   and the app then shows the victory screen.

## Known limitations (by design)

This version deliberately has **no Python game state** so it can be compared with Version 2:

- memory is only the chat transcript, so earlier actions can be forgotten or contradicted;
- the model can invent objects or accept actions that should be impossible;
- the solutions are inside the prompt, so they can be coaxed out;
- the escape is decided by a text marker the model writes;
- the game cannot be played when the API is unavailable.

See [../docs/testing.md](../docs/testing.md) for the test results.
