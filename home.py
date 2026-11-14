"""Overview page shown first in the combined launcher (streamlit_app.py)."""

import streamlit as st

from common import theme
from common.room_data import load_room

theme.apply_theme()
room = load_room()

theme.page_header(
    "MiniProject 01 - AI-Powered Escape Room",
    room["title"],
    "A text escape room where Google Gemini plays the Game Master. Two versions, one room.",
)

st.markdown(room["intro"])

left, right = st.columns(2, gap="large")
with left:
    theme.panel(
        "Version 1 - Interactive",
        theme.bullet_list(
            [
                "Gemini receives the whole story and the solutions in one system prompt.",
                "The chat history is the only memory.",
                "Gemini decides whether actions work and when you have escaped.",
                "Quick to build, but it can forget, invent or be talked out of the rules.",
            ],
            "",
        ),
    )
    st.page_link("version_1/app.py", label="Play Version 1", icon=":material/chat:")
with right:
    theme.panel(
        "Version 2 - Reliable",
        theme.bullet_list(
            [
                "Python holds the game state: inventory, clues, puzzles, locks.",
                "Every action is parsed and validated by Python before anything changes.",
                "Gemini only narrates results that Python has already decided.",
                "Solutions never enter the prompt, and the game still runs without the API.",
            ],
            "",
        ),
    )
    st.page_link("version_2/app.py", label="Play Version 2", icon=":material/verified_user:")

theme.panel(
    "Objects and goal",
    theme.bullet_list(
        [
            "Five main objects: study desk, old bookshelf, mysterious painting, locked drawer, exit door.",
            "Three linked puzzles lead to the four-digit code of the exit door.",
            "Type actions in plain English, for example 'examine the desk' or 'enter 1234 on the drawer'.",
        ],
        "",
    ),
)
