import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime

from backend.fetch_data import get_live_indices, get_index_last_price
from backend.predictor import get_featured_predictions, train_and_predict


@st.fragment(run_every=3)
def render_live_market_fragment():
    st.markdown("### 📊 Live Market Overview")
    st.caption(f"Live updating... (Last: {datetime.now().strftime('%H:%M:%S')})")
    
    indices = get_live_indices()
    c1, c2, c3 = st.columns(3)
    for col, key, label in zip(
        (c1, c2, c3), ("nifty", "banknifty", "sensex"), ("NIFTY 50", "BANK NIFTY", "SENSEX")
    ):
        info = indices.get(key)
        if info is None:
            col.metric(label, "N/A", "N/A")
        else:
            change_str = f"{info['change']} ({info['percent']}%)"
            col.metric(label, f"₹{info['price']}", f"{info['change']} ({info['percent']}%)")

def render_home():
    # Home page content: live indices, featured predictions, quick analysis
    st.markdown("## 🏠 Home – Live Market & Quick AI Insights")

    # Live Market Section (Auto-updating fragment)
    render_live_market_fragment()

    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    st.markdown("<div class='quick-actions'>", unsafe_allow_html=True)
    qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)
    with qa1:
        if st.button("🔮 Predictions", key="qa_pred", use_container_width=True):
            st.session_state["current_page"] = "Predictions"
            st.rerun()
    with qa2:
        if st.button("📉 Indicators", key="qa_ind", use_container_width=True):
            st.session_state["current_page"] = "Indicators"
            st.rerun()
    with qa3:
        if st.button("🧭 Screener", key="qa_scr", use_container_width=True):
            st.session_state["current_page"] = "Screener"
            st.rerun()
    with qa4:
        if st.button("⭐ Watchlist", key="qa_wl", use_container_width=True):
            st.session_state["current_page"] = "Watchlist"
            st.rerun()
    with qa5:
        if st.button("📰 News", key="qa_news", use_container_width=True):
            st.session_state["current_page"] = "News"
            st.rerun()
    with qa6:
        if st.button("📊 Analytics", key="qa_analytics", use_container_width=True):
            st.session_state["current_page"] = "Analytics"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Search Box Section
    st.markdown("---")
    st.markdown("### 🔎 Check Stock Price")
    
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_symbol = st.text_input("Enter Stock Name (e.g. RELIANCE, TCS)", placeholder="Type stock symbol...", key="stock_search_box")
    with col_btn:
        st.write("") 
        st.write("")
        search_clicked = st.button("Search", key="stock_search_btn")

    if search_symbol:
        # Heuristic to handle Indian stocks if user forgets suffix
        symbol_to_check = search_symbol.upper().strip()
        
        # Display a loading spinner
        with st.spinner(f"Fetching data for {symbol_to_check}..."):
            data = get_index_last_price(symbol_to_check)
            
            # If not found, try appending .NS (NSE)
            if not data and "." not in symbol_to_check:
                symbol_to_check = f"{symbol_to_check}.NS"
                data = get_index_last_price(symbol_to_check)
            
            # If still not found, try .BO (BSE)
            if not data and ".NS" in symbol_to_check:
                symbol_to_check = symbol_to_check.replace(".NS", ".BO")
                data = get_index_last_price(symbol_to_check)

        if data:
            st.success(f"Found: {symbol_to_check}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Price", f"₹{data['price']}")
            m2.metric("Change", f"{data['change']}")
            m3.metric("% Change", f"{data['percent']}%")

            st.markdown("#### ⚡ Actions")
            st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
            c_pred, c_ind = st.columns(2)
            with c_pred:
                if st.button("🚀 View AI Prediction", key="home_btn_pred", use_container_width=True):
                    st.session_state["selected_symbol"] = symbol_to_check
                    st.session_state["current_page"] = "Predictions"
                    st.session_state["prediction_auto_run"] = True
                    st.rerun()
            with c_ind:
                if st.button("📉 View Indicators", key="home_btn_ind", use_container_width=True):
                    st.session_state["selected_symbol"] = symbol_to_check
                    st.session_state["current_page"] = "Indicators"
                    st.session_state["indicators_auto_run"] = True
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.error(f"Could not find data for '{search_symbol}'. Please check the symbol.")

    st.markdown("---")
    st.markdown("### ⭐ Featured AI Predictions")
    
    # Cache featured predictions to avoid re-training on every refresh if possible, 
    # but for now we'll fetch fresh to keep it simple and up-to-date.
    featured = get_featured_predictions()
    
    if not featured:
        st.info("Could not fetch featured stocks. Check internet connection.")
    else:
        cols = st.columns(len(featured))
        for col, item in zip(cols, featured):
            with col:
                st.markdown("<div class='ai-card'>", unsafe_allow_html=True)
                st.markdown(f"**{item['symbol']}**", unsafe_allow_html=True)
                st.write(f"Last close: ₹{item['last_close']}")
                st.write(f"Avg next 7 days: ₹{item['avg_future']}")
                badge_class = {
                    "BUY": "ai-badge-buy",
                    "SELL": "ai-badge-sell",
                    "HOLD": "ai-badge-hold",
                }.get(item["signal"], "ai-badge-hold")
                st.markdown(
                    f"<span class='{badge_class}'>Signal: {item['signal']}</span>",
                    unsafe_allow_html=True,
                )

                dfp = pd.DataFrame(item["predictions"])
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=dfp["date"],
                        y=dfp["price"],
                        mode="lines+markers",
                        name="Predicted",
                        line=dict(color="#38bdf8", width=2)
                    )
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0), 
                    height=200,
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Quick Stock Analysis")
    q1, q2 = st.columns([3, 1])
    with q1:
        symbol = st.text_input(
            "Enter NSE stock symbol (e.g., TCS.NS, INFY.NS)", "TCS.NS"
        )
    with q2:
        run_analysis = st.button("Analyze")

    if run_analysis and symbol:
        from backend.db import log_search
        user = st.session_state.get("user")
        log_search(user["id"] if user else None, symbol)
        
        with st.spinner(f"Analyzing {symbol}..."):
            res = train_and_predict(symbol)
            
        if res is None:
            st.error("No data found for this symbol.")
        else:
            st.markdown(f"#### {res['symbol']} – 7-Day Prediction Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Last Close", f"₹{res['last_close']}")
            c2.metric("Avg Predicted", f"₹{res['avg_future']}")
            c3.metric("AI Signal", res["signal"])
            dfp = pd.DataFrame(res["predictions"])
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=dfp["date"], y=dfp["price"], mode="lines+markers", line=dict(color="#22c55e"))
            )
            fig.update_layout(
                title="Next 7 Days Predicted Price",
                xaxis_title="Date",
                yaxis_title="Price",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
