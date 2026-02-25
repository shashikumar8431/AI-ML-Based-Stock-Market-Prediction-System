import streamlit as st
from backend.db import authenticate_user, register_user
from . import session


def auth_sidebar():
    session.ensure_session()
    st.sidebar.markdown("<p class='sidebar-title'>👤 Account</p>", unsafe_allow_html=True)

    user = session.current_user()
    if user is None:
        mode = st.sidebar.selectbox("Login / Register", ["Login", "Register"])
        if mode == "Login":
            email = st.sidebar.text_input("Email")
            pwd = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Login"):
                usr = authenticate_user(email, pwd)
                if usr:
                    session.set_user(usr)
                    st.sidebar.success("Logged in.")
                else:
                    st.sidebar.error("Invalid email or password.")
        else:
            name = st.sidebar.text_input("Name")
            email = st.sidebar.text_input("Email")
            pwd = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Register"):
                ok, msg = register_user(name, email, pwd)
                if ok:
                    st.sidebar.success(msg)
                else:
                    st.sidebar.error(msg)
    else:
        st.sidebar.write(f"Logged in as **{user['email']}**")
        if st.sidebar.button("Logout"):
            session.logout()
            st.sidebar.success("Logged out.")
