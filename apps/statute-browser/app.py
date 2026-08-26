from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
PAGES = APP_DIR / "app_pages"
# Pages are exec'd as scripts, so `loader` and `shared` have to be importable by name.
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

st.set_page_config(
    page_title="Draftly statute browser",
    page_icon=":material/account_balance:",
    layout="wide",
)

navigation = st.navigation(
    [
        st.Page(PAGES / "overview.py", title="Corpus overview", icon=":material/dataset:", default=True),
        st.Page(PAGES / "statute.py", title="Statute browser", icon=":material/menu_book:"),
        st.Page(PAGES / "amending_acts.py", title="Amending Acts", icon=":material/history_edu:"),
    ]
)
navigation.run()
