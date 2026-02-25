import streamlit as st
from auth import session
from backend.db import get_user_searches


def render_analytics():
    session.ensure_session()
    user = session.current_user()
    st.markdown("## 📊 User Analytics")
    if not user:
        st.warning("Login to view your analytics.")
        return
    rows = get_user_searches(user["id"])
    if not rows:
        st.info("No recent searches.")
        return
    for sym, ts in rows:
        st.write(f"{ts} — {sym}")

