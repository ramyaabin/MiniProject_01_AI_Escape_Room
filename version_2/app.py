"""Version 2 - Reliable AI Escape Room (Streamlit page).

Run on its own:      streamlit run version_2/app.py
Or with Version 1:   streamlit run streamlit_app.py
"""

import sys
from pathlib import Path

# Make "common" and "version_2" importable when this file is run directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from common import theme  # noqa: E402
from common.llm_client import GeminiClient  # noqa: E402
from common.room_data import load_room  # noqa: E402
from version_2.action_parser import build_alias_table, parse_action  # noqa: E402
from version_2.game_engine import process_turn, restart_game  # noqa: E402
from version_2.game_master import GameMasterV2  # noqa: E402
from common.room_scene import render_room_svg  # noqa: E402
from version_2.game_state import public_view, puzzles_solved, scene_view, to_json  # noqa: E402

# Every session key starts with "v2_" so both versions can share one browser session.
STATE_KEY = "v2_state"
MESSAGES_KEY = "v2_messages"
NOTICE_KEY = "v2_notice"


def get_services():
    """Create the room, LLM client and narrator once per browser session."""
    if "v2_room" not in st.session_state:
        room = load_room()
        llm = GeminiClient()
        st.session_state.v2_room = room
        st.session_state.v2_alias_table = build_alias_table(room)
        st.session_state.v2_llm = llm
        st.session_state.v2_game_master = GameMasterV2(llm, room)
    return (st.session_state.v2_room, st.session_state.v2_alias_table,
            st.session_state.v2_llm, st.session_state.v2_game_master)


def start_new_game(room: dict) -> None:
    st.session_state[STATE_KEY] = restart_game(room)
    st.session_state[MESSAGES_KEY] = []
    st.session_state[NOTICE_KEY] = None


def handle_player_message(text: str) -> None:
    room, alias_table, llm, game_master = get_services()
    text = text.strip()
    if not text:
        st.session_state[NOTICE_KEY] = "Please type an action, for example 'examine the desk'."
        return

    # 1. Understand the sentence   2. Python validates and applies it   3. Gemini narrates
    action = parse_action(text, room, alias_table, llm)
    new_state, result = process_turn(st.session_state[STATE_KEY], room, action)
    narration, source = game_master.narrate(text, result, new_state)

    st.session_state[STATE_KEY] = new_state
    st.session_state[NOTICE_KEY] = None
    st.session_state[MESSAGES_KEY] += [
        {"role": "user", "text": text},
        {"role": "assistant", "text": narration, "action": result["action"],
         "success": result["success"], "outcome": result["outcome"], "source": source},
    ]


def describe_engine_decision(message: dict) -> str:
    action = message["action"]
    parts = [action["verb"]]
    if action.get("item"):
        parts.append(action["item"])
    if action.get("target"):
        parts.append(("on " if action.get("item") else "") + action["target"])
    if action.get("code"):
        parts.append(f"code {action['code']}")
    verdict = "accepted" if message["success"] else f"rejected: {message['outcome']}"
    narrator = "Gemini narration" if message["source"] == "gemini" else "built-in narration"
    return f"Engine: {' '.join(parts)} -> {verdict} | {narrator}"


def render_side_panel(state: dict, room: dict, llm) -> None:
    door = theme.badge("Door open", "open") if not state["door_locked"] else theme.badge("Door locked", "locked")
    drawer = theme.badge("Drawer open", "open") if not state["drawer_locked"] else theme.badge("Drawer locked", "locked")
    theme.panel("Game status", f"{door}{drawer}{theme.badge('Turn ' + str(state['turn']))}")

    puzzle_rows = [(room["puzzles"][pid]["title"], solved) for pid, solved in state["puzzles"].items()]
    puzzle_rows.append(("Final challenge: the exit door", state["escaped"]))
    theme.panel(f"Trials ({puzzles_solved(state)}/3)", theme.progress_steps(puzzle_rows))

    view = public_view(state, room)
    theme.panel("Inventory", theme.bullet_list([n.capitalize() for n in view["inventory"]], "Empty for now."))
    theme.panel("Discovered clues", theme.bullet_list(view["discovered_clues"], "No clues yet. Examine things."))

    llm_status = f"Gemini: {llm.model}" if llm.is_configured else "Gemini off: built-in narration"
    theme.panel("Game Master", f"<div class='er-muted'>{llm_status}</div>")

    if st.button("Restart game", key="v2_restart", width="stretch"):
        start_new_game(room)
        st.rerun()

    with st.expander("Engine view (structured state)"):
        st.caption("This is the Python game state. The LLM can read a filtered copy but can never change it.")
        st.code(to_json({k: v for k, v in state.items() if k != "history"}), language="json")


def main() -> None:
    theme.apply_theme()
    room, _, llm, _ = get_services()
    if STATE_KEY not in st.session_state:
        start_new_game(room)
    state = st.session_state[STATE_KEY]

    theme.page_header(
        "Version 2 - Reliable AI Escape Room",
        "The Mystery of the Forgotten Library",
        "Python enforces the rules and keeps the game state. Gemini narrates what Python has decided.",
    )

    with st.expander("How to play", expanded=not st.session_state[MESSAGES_KEY]):
        st.markdown(
            "- Type actions in plain English: *look around*, *examine the bookshelf*, *read the journal*, "
            "*take the brass key*, *use the key on the painting*, *enter 1234 on the drawer*.\n"
            "- Type *inventory* to see what you carry, or *hint* if you are stuck.\n"
            "- Inventory, clues and puzzle progress on the right always show the real game state.\n"
            "- Use **Restart game** at any time to start again."
        )
    if not llm.is_configured:
        st.info("No Gemini API key found, so Version 2 is running with its built-in narration. "
                "All rules, puzzles and the escape still work. Add GEMINI_API_KEY to .env for AI narration.")

    if state["escaped"]:
        attempts = state["failed_attempts"]["drawer"] + state["failed_attempts"]["door"]
        theme.escape_screen(
            "You escaped the Forgotten Library",
            f"Escape confirmed by the game engine after {state['turn']} turns and "
            f"{attempts} wrong code attempts. Press Restart game to play again.",
        )
    theme.room_picture(render_room_svg(scene_view(state, room)))
    st.caption("The room is drawn from the Python game state and updates as you play.")

    chat_col, side_col = st.columns([2.2, 1], gap="large")
    with side_col:
        render_side_panel(state, room, llm)

    with chat_col:
        chat_box = st.container(height=460, border=False)
        with chat_box:
            with st.chat_message("assistant", avatar=theme.GM_AVATAR):
                st.markdown(f"{room['intro']}\n\n{room['room_description']}\n\nWhat would you like to do?")
            for message in st.session_state[MESSAGES_KEY]:
                if message["role"] == "user":
                    with st.chat_message("user", avatar=theme.PLAYER_AVATAR):
                        st.markdown(message["text"])
                else:
                    with st.chat_message("assistant", avatar=theme.GM_AVATAR):
                        st.markdown(message["text"])
                        st.caption(describe_engine_decision(message))
        if st.session_state[NOTICE_KEY]:
            st.warning(st.session_state[NOTICE_KEY])

    text = st.chat_input("What do you do?", key="v2_input", max_chars=400, disabled=state["escaped"])
    if text is not None:
        with st.spinner("The Game Master is thinking..."):
            handle_player_message(text)
        st.rerun()


main()
