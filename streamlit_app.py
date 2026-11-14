"""Combined launcher: one Streamlit app with a page for each version.

    streamlit run streamlit_app.py

Each version can also be run on its own (see README.md).
"""

import streamlit as st

st.set_page_config(
    page_title="AI Escape Room",
    page_icon=":material/auto_stories:",
    layout="wide",
)

pages = st.navigation(
    [
        st.Page("home.py", title="Overview", icon=":material/home:", default=True),
        st.Page("version_1/app.py", title="Version 1 - Interactive", icon=":material/chat:",
                url_path="version-1"),
        st.Page("version_2/app.py", title="Version 2 - Reliable", icon=":material/verified_user:",
                url_path="version-2"),
    ]
)
pages.run()
