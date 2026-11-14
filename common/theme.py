"""Visual theme shared by both versions: dark library, warm gold accents.

Colours come from .streamlit/config.toml. This file only adds a little CSS
for typography and a few reusable HTML blocks (header, panels, escape screen).
"""

from __future__ import annotations

import html

import streamlit as st

GM_AVATAR = ":material/auto_stories:"
PLAYER_AVATAR = ":material/person:"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');

html, body, [class*="st-"], .stMarkdown, .stChatMessage {
    font-family: 'Source Serif 4', Georgia, serif;
}
h1, h2, h3, .er-title {
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    letter-spacing: 0.01em;
}
.block-container { padding-top: 2.2rem; max-width: 1200px; }

.er-header { border-bottom: 1px solid #4a3a25; padding-bottom: 0.9rem; margin-bottom: 1.1rem; }
.er-kicker { color: #c9a24a; text-transform: uppercase; letter-spacing: 0.18em; font-size: 0.75rem; }
.er-title { font-size: 2.4rem; font-weight: 700; color: #f1e6cc; margin: 0.15rem 0 0.25rem 0; line-height: 1.1; }
.er-subtitle { color: #b8a888; font-size: 1rem; }

.er-panel {
    background: #221a12; border: 1px solid #4a3a25; border-radius: 8px;
    padding: 0.8rem 1rem; margin-bottom: 0.8rem;
}
.er-panel h4 {
    font-family: 'Cormorant Garamond', Georgia, serif; color: #c9a24a;
    font-size: 1.15rem; margin: 0 0 0.45rem 0; font-weight: 700;
}
.er-panel ul { margin: 0; padding-left: 1.1rem; }
.er-panel li { margin-bottom: 0.25rem; font-size: 0.92rem; }
.er-muted { color: #8f8068; font-size: 0.9rem; font-style: italic; }

.er-step { display: flex; align-items: flex-start; gap: 0.55rem; margin-bottom: 0.4rem; font-size: 0.92rem; }
.er-dot {
    flex: none; width: 0.85rem; height: 0.85rem; margin-top: 0.25rem; border-radius: 50%;
    border: 2px solid #6b5636;
}
.er-dot.done { background: #c9a24a; border-color: #c9a24a; }
.er-step.done .er-step-title { color: #f1e6cc; }
.er-step .er-step-title { color: #a8987a; }

.er-badge {
    display: inline-block; padding: 0.1rem 0.55rem; border-radius: 999px; font-size: 0.8rem;
    border: 1px solid #6b5636; color: #d8c9a6; margin-right: 0.3rem;
}
.er-badge.locked { border-color: #8a3b2e; color: #e0a79a; }
.er-badge.open { border-color: #c9a24a; color: #f1d58f; }

.er-escape {
    border: 1px solid #c9a24a; border-radius: 10px; padding: 1.4rem 1.6rem; margin: 0.5rem 0 1rem 0;
    background: linear-gradient(180deg, #2c2215 0%, #1d160f 100%); text-align: center;
}
.er-escape .er-title { font-size: 2.1rem; color: #f1d58f; }

[data-testid="stChatMessage"] { background: #1e1710; border: 1px solid #33281b; border-radius: 8px; }
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"<div class='er-header'><div class='er-kicker'>{html.escape(kicker)}</div>"
        f"<div class='er-title'>{html.escape(title)}</div>"
        f"<div class='er-subtitle'>{html.escape(subtitle)}</div></div>",
        unsafe_allow_html=True,
    )


def panel(title: str, body_html: str) -> None:
    """A bordered side panel. body_html must already be escaped by the caller."""
    st.markdown(
        f"<div class='er-panel'><h4>{html.escape(title)}</h4>{body_html}</div>",
        unsafe_allow_html=True,
    )


def bullet_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f"<div class='er-muted'>{html.escape(empty_text)}</div>"
    return "<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in items) + "</ul>"


def progress_steps(steps: list[tuple[str, bool]]) -> str:
    rows = []
    for title, done in steps:
        css = "er-step done" if done else "er-step"
        dot = "er-dot done" if done else "er-dot"
        rows.append(
            f"<div class='{css}'><span class='{dot}'></span>"
            f"<span class='er-step-title'>{html.escape(title)}</span></div>"
        )
    return "".join(rows)


def badge(text: str, kind: str = "") -> str:
    return f"<span class='er-badge {kind}'>{html.escape(text)}</span>"


def escape_screen(headline: str, details: str) -> None:
    st.markdown(
        f"<div class='er-escape'><div class='er-kicker'>Game complete</div>"
        f"<div class='er-title'>{html.escape(headline)}</div>"
        f"<div class='er-subtitle'>{html.escape(details)}</div></div>",
        unsafe_allow_html=True,
    )
