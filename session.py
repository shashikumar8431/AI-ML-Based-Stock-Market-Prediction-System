import streamlit as st


def ensure_session():
    if "user" not in st.session_state:
        st.session_state["user"] = None


def current_user():
    return st.session_state.get("user")


def set_user(user):
    st.session_state["user"] = user


def logout():
    st.session_state["user"] = None


def is_logged_in():
    return st.session_state.get("user") is not None
