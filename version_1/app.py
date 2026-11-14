"""Version 1 - Interactive AI Escape Room (Streamlit page).

Run on its own:      streamlit run version_1/app.py
Or with Version 2:   streamlit run streamlit_app.py
"""

import sys
from pathlib import Path

# Make "common" and "version_1" importable when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from common import theme  # noqa: E402
from common.llm_client import GeminiClient, LLMError  # noqa: E402
from version_1.game_master import GameMasterV1  # noqa: E402

# Every session key starts with "v1_" so Version 1 and Version 2 can share one browser session.
HISTORY_KEY = "v1_history"
ESCAPED_KEY = "v1_escaped"
ERROR_KEY = "v1_error"


def get_game_master() -> GameMasterV1:
    if "v1_game_master" not in st.session_state:
        st.session_state.v1_game_master = GameMasterV1(GeminiClient())
    return st.session_state.v1_game_master


def restart_game() -> None:
    st.session_state[HISTORY_KEY] = []
    st.session_state[ESCAPED_KEY] = False
    st.session_state[ERROR_KEY] = None


def handle_player_message(game_master: GameMasterV1, message: str) -> None:
    message = message.strip()
    if not message:
        st.session_state[ERROR_KEY] = "Please type an action, for example 'examine the desk'."
        return
    history = st.session_state[HISTORY_KEY]
    try:
        reply, escaped = game_master.respond(history, message)
    except LLMError as error:
        # The player's message is not stored, so they can simply try again.
        st.session_state[ERROR_KEY] = str(error)
        return
    history.append({"role": "user", "text": message})
    history.append({"role": "model", "text": reply})
    st.session_state[ERROR_KEY] = None
    if escaped:
        st.session_state[ESCAPED_KEY] = True


def render_side_panel(game_master: GameMasterV1) -> None:
    player_turns = len(st.session_state[HISTORY_KEY]) // 2
    status = theme.badge("Escaped", "open") if st.session_state[ESCAPED_KEY] else theme.badge("Trapped", "locked")
    theme.panel(
        "Game status",
        f"{status}{theme.badge(f'{player_turns} turns')}"
        "<div class='er-muted' style='margin-top:0.5rem'>Version 1 keeps no structured state. "
        "Everything you have found exists only in the conversation, and Gemini alone decides "
        "what happens.</div>",
    )
    theme.panel(
        "Objects in the room",
        theme.bullet_list(
            ["Study desk", "Old bookshelf", "Mysterious painting", "Locked drawer", "Exit door"],
            "",
        ),
    )
    llm = game_master.llm
    theme.panel(
        "Game Master",
        f"<div class='er-muted'>Model: {llm.model}<br>"
        f"API key: {'configured' if llm.is_configured else 'missing'}</div>",
    )
    if st.button("Restart game", key="v1_restart", width="stretch"):
        restart_game()
        st.rerun()


def main() -> None:
    theme.apply_theme()
    if HISTORY_KEY not in st.session_state:
        restart_game()
    game_master = get_game_master()

    theme.page_header(
        "Version 1 - Interactive AI Escape Room",
        "The Mystery of the Forgotten Library",
        "Gemini is the Game Master. Explore the room in plain English, solve three puzzles and escape.",
    )

    with st.expander("How to play", expanded=not st.session_state[HISTORY_KEY]):
        st.markdown(
            "- Type what you want to do, in your own words: *look around*, *examine the bookshelf*, "
            "*take the key*, *enter 1234 on the drawer*.\n"
            "- Examine objects closely. Clues are only revealed when you look in the right place.\n"
            "- Solve the three puzzles to learn the four-digit code for the exit door.\n"
            "- Use **Restart game** at any time to start again."
        )

    chat_col, side_col = st.columns([2.2, 1], gap="large")

    with side_col:
        render_side_panel(game_master)

    with chat_col:
        if not game_master.llm.is_configured:
            st.error(
                "Version 1 needs Gemini to run. Copy `.env.example` to `.env`, add your "
                "GEMINI_API_KEY and restart Streamlit."
            )
        if st.session_state[ESCAPED_KEY]:
            theme.escape_screen(
                "You escaped the Forgotten Library",
                "The Game Master says the door is open. (In Version 1 this is the LLM's decision.)",
            )

        chat_box = st.container(height=520, border=False)
        with chat_box:
            with st.chat_message("assistant", avatar=theme.GM_AVATAR):
                st.markdown(game_master.opening_message())
            for turn in st.session_state[HISTORY_KEY]:
                role = "user" if turn["role"] == "user" else "assistant"
                avatar = theme.PLAYER_AVATAR if role == "user" else theme.GM_AVATAR
                with st.chat_message(role, avatar=avatar):
                    st.markdown(turn["text"])

        if st.session_state[ERROR_KEY]:
            st.warning(st.session_state[ERROR_KEY])

    disabled = st.session_state[ESCAPED_KEY] or not game_master.llm.is_configured
    message = st.chat_input("What do you do?", key="v1_input", max_chars=400, disabled=disabled)
    if message is not None:
        with st.spinner("The Game Master is thinking..."):
            handle_player_message(game_master, message)
        st.rerun()


main()
