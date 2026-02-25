import streamlit as st
from backend.db import init_db, authenticate_user, register_user, get_user_stats, reset_password, update_user_name, change_password
from auth import session
from sections.home import render_home
from sections.prediction import render_prediction
from sections.indicators import render_indicators
from sections.watchlist import render_watchlist
from sections.screener import render_screener
from sections.portfolio import render_portfolio
from sections.heatmap import render_heatmap
from sections.news import render_news
from sections.analytics import render_analytics

# Page config (hide sidebar, wide layout)
st.set_page_config(
    page_title="AI & ML Based Stock Market Prediction System",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load existing CSS (if present)
try:
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Inject global custom CSS for theme, fonts, and navbar
st.markdown(
    """
    <style>
      /* === Global Typography & Background === */
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
      html, body, [data-testid="stAppViewContainer"] { background: #f4f6fb; font-family: 'Poppins', sans-serif; }
      .stApp { background: #f4f6fb !important; }

      /* === Layout Container === */
      [data-testid="block-container"] { max-width: 1200px; padding-top: 0.75rem; padding-bottom: 3rem; }
      header, [data-testid="stToolbar"] { display: none !important; }
      section[data-testid="stSidebar"], div[data-testid="stSidebarNav"] { display: none !important; }

      /* === Navbar === */
      .app-navbar { position: sticky; top: 0; z-index: 1000; width: 100%; padding: 0.6rem 1rem; background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 50%, #60a5fa 100%); color: #ffffff; box-shadow: 0 6px 18px rgba(0,0,0,0.14); border-bottom: 1px solid rgba(255,255,255,0.15); }
      .navbar-content { display: block; }
      .navbar-title-single { text-align: center; font-weight: 800; font-size: 1.6rem; letter-spacing: 0.2px; white-space: nowrap; }
      .navbar-row { margin-top: 6px; }

      /* Left: Logo + Title */
      .nav-left { display: flex; align-items: center; gap: 10px; }
      .logo { font-size: 1.25rem; line-height: 1; }
      .title-text { display: flex; flex-direction: column; }
      .title-line1 { font-size: 1.05rem; font-weight: 700; letter-spacing: 0.2px; }
      .title-line2 { font-size: 0.92rem; opacity: 0.95; }

      /* Center: Navigation Buttons */
      .nav-center { display: flex; flex-direction: row; justify-content: flex-start; align-items: center; gap: 12px; white-space: nowrap; flex-wrap: nowrap; overflow-x: auto; }
      .nav-center > div { display: inline-flex !important; flex: 0 0 auto !important; width: auto !important; margin: 0 6px !important; padding: 0 !important; }
      .nav-center div.stButton { display: inline-flex; margin: 0 6px; vertical-align: middle; width: auto; flex: 0 0 auto; }
      .nav-center div.stButton > button { 
        background: linear-gradient(180deg, #ffffff, #f8fafc) !important; 
        color: #0f172a !important; 
        border: 1px solid #e5e7eb !important; 
        border-radius: 999px !important; 
        padding: 12px 20px !important; 
        font-weight: 700 !important; 
        white-space: nowrap !important; 
        min-width: 160px !important; 
        box-shadow: 0 12px 20px rgba(15,23,42,0.12) !important;
        transition: transform 120ms ease, box-shadow 160ms ease;
      }
      .nav-center div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 16px 26px rgba(15,23,42,0.15) !important; }
      .nav-center div[data-testid="stPopover"] { display: inline-block; margin: 0 6px; vertical-align: middle; }
      /* Navbar pills: white style to match image */
      .nav-center div.stButton > button { 
        background: #ffffff !important; 
        color: #0f172a !important; 
        border: 1px solid #e5e7eb !important; 
        border-radius: 999px !important; 
        padding: 10px 18px !important; 
        font-weight: 700 !important; 
        white-space: nowrap !important; 
        min-width: 110px !important;
        box-shadow: 0 6px 16px rgba(15,23,42,0.08) !important;
      }

      /* Right: Profile Container */
      .nav-right { display: flex; justify-content: flex-end; align-items: center; }
      .profile-text { font-size: 0.9rem; color: #0f172a; opacity: 0.85; margin-right: 8px; }
      /* Style profile trigger like quick actions */
      .nav-right div.stButton > button { 
        background: linear-gradient(180deg, #ffffff, #f8fafc) !important; 
        color: #0f172a !important; 
        border: 1px solid #e5e7eb !important; 
        border-radius: 999px !important; 
        padding: 10px 18px !important; 
        font-weight: 700 !important; 
        box-shadow: 0 12px 20px rgba(15,23,42,0.12) !important;
      }
      .nav-right div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 16px 26px rgba(15,23,42,0.15) !important; }

      /* === Content Spacing === */
      .content-spacer { height: 12px; }
      h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { font-weight: 700; color: #0f172a; }

      /* === Cards & Components (Light) === */
      .ai-card { background: #ffffff; border-radius: 14px; padding: 16px 18px; border: 1px solid rgba(2,132,199,0.15); box-shadow: 0 8px 22px rgba(2,132,199,0.10); margin-bottom: 14px; }
      .ai-badge-buy { color: #16a34a; font-weight: 600; } .ai-badge-sell { color: #dc2626; font-weight: 600; } .ai-badge-hold { color: #ca8a04; font-weight: 600; }
      .stMetric { background: #ffffff; padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(2,132,199,0.12); box-shadow: 0 4px 12px rgba(2,132,199,0.08); }
      .stPlotlyChart { background: #ffffff; padding: 8px; border-radius: 12px; border: 1px solid rgba(2,132,199,0.12); box-shadow: 0 4px 12px rgba(2,132,199,0.08); }

      /* === Inputs & Buttons === */
      input[type="text"], input[type="email"], input[type="password"], textarea { border-radius: 10px !important; border: 1px solid rgba(2,132,199,0.25) !important; }
      button[kind="primary"], .stButton>button { border-radius: 999px !important; padding: 0.5rem 1rem !important; box-shadow: 0 4px 12px rgba(37,99,235,0.22) !important; }

      /* === Home Quick Actions === */
      .quick-actions { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; width: 100%; background: #ffffff; border: 1px solid rgba(226,232,240,0.8); box-shadow: 0 14px 28px rgba(2,132,199,0.10), 0 2px 4px rgba(2,132,199,0.06); border-radius: 20px; padding: 14px 16px; margin-bottom: 14px; }
      .quick-actions > div { display: inline-flex !important; flex: 0 0 auto !important; width: auto !important; margin: 0 !important; }
      .quick-actions div.stButton > button { 
        background: linear-gradient(180deg, #ffffff, #f8fafc) !important; 
        color: #0f172a !important; 
        border: 1px solid #e5e7eb !important; 
        border-radius: 999px !important; 
        padding: 12px 20px !important; 
        font-weight: 700 !important; 
        white-space: nowrap !important; 
        min-width: 160px !important; 
        box-shadow: 0 12px 20px rgba(15,23,42,0.12) !important;
      }
      .quick-actions div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 16px 26px rgba(15,23,42,0.15) !important; }

      /* === Search Action Buttons === */
      .action-buttons { display: block; width: 100%; }
      .action-buttons > div { display: inline-flex !important; flex: 0 0 auto !important; width: auto !important; }
      .action-buttons div.stButton > button { 
        background: #ffffff !important; 
        color: #0f172a !important; 
        border: 1px solid #e5e7eb !important; 
        border-radius: 999px !important; 
        padding: 10px 16px !important; 
        font-weight: 700 !important; 
        min-width: 160px !important; 
        box-shadow: 0 6px 16px rgba(15,23,42,0.08) !important;
      }

      /* === Responsive === */
      @media (max-width: 860px) {
        .navbar-content { grid-template-columns: 1fr; gap: 8px; }
        .nav-right { justify-content: center; }
        .nav-center { flex-wrap: nowrap; }
        .profile-card { width: 100%; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# Init DB
init_db()

# Ensure session keys for routing and auth state
session.ensure_session()
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Login"

# No URL-based routing; keep everything in a single page using session_state only

with st.container():
    st.markdown('<div class="app-navbar"><div class="navbar-content">', unsafe_allow_html=True)
    st.markdown("<div class='navbar-title-single'>💹 AI & ML Based Stock Market Prediction System</div>", unsafe_allow_html=True)
    st.markdown("<div class='navbar-row'>", unsafe_allow_html=True)
    left, middle, right = st.columns([0.3, 2.0, 0.7])

    # Center section: navigation buttons (forced horizontal using columns)
    with middle:
        current = st.session_state.get("current_page", "Home")
        labels = ["Home","Predictions","Indicators","Watchlist","Screener","Portfolio","Heatmap","News","Analytics"]
        display_labels = ["🏠 Home","🔮 Predictions","📉 Indicators","⭐ Watchlist","🧭 Screener","💼 Portfolio","🔥 Heatmap","📰 News","📈 Analytics"]
        cols = st.columns(len(labels))
        for i, (col, label) in enumerate(zip(cols, labels)):
            with col:
                if st.button(display_labels[i], key=f"nav_{label.lower()}"):
                    st.session_state["current_page"] = label
                    st.session_state["profile_center_open"] = False

    # Right section: profile trigger only (opens centered panel)
    with right:
        user = session.current_user()
        status_text = (f"Hi, {user['name']}" if user else "Guest")
        sub_text = (user["email"] if user else "Not logged in")
        trigger_label = f"👤 {user['name']}" if user else "👤 Profile"
        if st.button(trigger_label, key="profile_trigger"):
            st.session_state["profile_center_open"] = True
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="content-spacer"></div>', unsafe_allow_html=True)

# Centered profile panel
if st.session_state.get("profile_center_open"):
    l, m, r = st.columns([1, 1.5, 1])
    with m:
        with st.container(border=True):
            c_head, c_close = st.columns([8, 1])
            with c_head:
                st.markdown("### 👤 User Profile")
            with c_close:
                if st.button("❌", key="close_x_profile"):
                    st.session_state["profile_center_open"] = False
                    st.rerun()

            user = session.current_user()
            if user is None:
                tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])
                with tab_login:
                    st.write("")
                    email = st.text_input("Email Address", key="login_email")
                    pwd = st.text_input("Password", type="password", key="login_pwd")
                    st.write("")
                    if st.button("Login Now", key="login_btn", use_container_width=True, type="primary"):
                        usr = authenticate_user(email, pwd)
                        if usr:
                            session.set_user(usr)
                            st.success(f"Welcome back, {usr['name']}!")
                            st.session_state["profile_center_open"] = False
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                    with st.expander("Forgot Password"):
                        fp_email = st.text_input("Registered Email", key="fp_email")
                        fp_new = st.text_input("New Password", type="password", key="fp_new")
                        fp_conf = st.text_input("Confirm New Password", type="password", key="fp_conf")
                        if st.button("Reset Password", key="btn_fp_reset", use_container_width=True):
                            if not fp_email or not fp_new or not fp_conf:
                                st.error("All fields are required.")
                            elif fp_new != fp_conf:
                                st.error("Passwords do not match.")
                            else:
                                ok, msg = reset_password(fp_email, fp_new)
                                if ok:
                                    st.success(msg)
                                else:
                                    st.error(msg)
                with tab_register:
                    st.write("")
                    name = st.text_input("Full Name", key="reg_name")
                    email = st.text_input("Email Address", key="reg_email")
                    pwd = st.text_input("Password", type="password", key="reg_pwd")
                    st.write("")
                    if st.button("Create Account", key="register_btn", use_container_width=True, type="primary"):
                        if name and email and pwd:
                            ok, msg = register_user(name, email, pwd)
                            if ok:
                                st.success(msg + " Please switch to Login tab.")
                            else:
                                st.error(msg)
                        else:
                            st.error("All fields are required.")
            else:
                st.markdown(f"""
                <div style="text-align: center; padding: 20px 0;">
                    <div style="font-size: 4rem; margin-bottom: 10px;">👨‍💼</div>
                    <div style="font-size: 1.6rem; font-weight: 700; color: #1e293b;">{user['name']}</div>
                    <div style="color: #64748b; font-size: 0.95rem;">{user['email']}</div>
                </div>
                """, unsafe_allow_html=True)
                stats = get_user_stats(user["id"])
                st.markdown("#### 📊 Your Activity")
                s1, s2, s3 = st.columns(3)
                s1.metric("Watchlist", stats.get("watchlist_count", 0))
                s2.metric("Portfolio", stats.get("portfolio_count", 0))
                s3.metric("Searches", stats.get("search_count", 0))
                st.markdown("---")
                with st.expander("Edit Profile"):
                    new_name = st.text_input("Full Name", value=user["name"], key="edit_name")
                    if st.button("Save", key="btn_save_name"):
                        if new_name and new_name.strip():
                            ok = update_user_name(user["id"], new_name.strip())
                            if ok:
                                user["name"] = new_name.strip()
                                session.set_user(user)
                                st.success("Profile updated.")
                            else:
                                st.error("Update failed.")
                        else:
                            st.error("Name cannot be empty.")
                with st.expander("Change Password"):
                    cur_pwd = st.text_input("Current Password", type="password", key="chg_cur")
                    new_pwd = st.text_input("New Password", type="password", key="chg_new")
                    conf_pwd = st.text_input("Confirm New Password", type="password", key="chg_conf")
                    if st.button("Change Password", key="btn_chg_pwd"):
                        if not cur_pwd or not new_pwd or not conf_pwd:
                            st.error("All fields are required.")
                        elif new_pwd != conf_pwd:
                            st.error("Passwords do not match.")
                        else:
                            ok, msg = change_password(user["id"], cur_pwd, new_pwd)
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
                    session.logout()
                    st.session_state["profile_center_open"] = False
                    st.rerun()

# No URL param sync; routing is controlled by session_state only

# Page routing
page = st.session_state.get("current_page", "Home")
if page == "Home":
    render_home()
elif page == "Predictions":
    render_prediction()
elif page == "Indicators":
    render_indicators()
elif page == "Watchlist":
    render_watchlist()
elif page == "Screener":
    render_screener()
elif page == "Portfolio":
    render_portfolio()
elif page == "Heatmap":
    render_heatmap()
elif page == "News":
    render_news()
elif page == "Analytics":
    render_analytics()
else:
    render_home()
