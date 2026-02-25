import streamlit as st
import yfinance as yf

from auth import session
from backend.db import upsert_portfolio, get_portfolio, get_cash_balance, get_symbol_qty


def get_last_price(symbol: str):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="1d")
        if hist is None or hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception:
        return None


def render_portfolio():
    session.ensure_session()
    user = session.current_user()
    st.markdown("## 💼 Portfolio")
    if not user:
        st.warning("Please login to use the portfolio simulator.")
        return

    st.markdown("""
    <style>
      :root {
        --bg: #0b1220;
        --card: rgba(255,255,255,0.12);
        --border: rgba(255,255,255,0.18);
        --text: #e5e7eb;
        --accent: #3b82f6;
        --accent2: #22c55e;
        --accent3: #f59e0b;
        --shadow: 0 20px 40px rgba(0,0,0,0.35);
      }
      @media (prefers-color-scheme: light) {
        :root {
          --bg: #f4f6fb;
          --card: rgba(255,255,255,0.65);
          --border: rgba(2,132,199,0.15);
          --text: #0f172a;
          --accent: #2563eb;
          --accent2: #16a34a;
          --accent3: #ca8a04;
          --shadow: 0 14px 28px rgba(2,132,199,0.12);
        }
      }
      .pf-container { display: block; }
      .pf-hero {
        position: relative;
        background: radial-gradient(1200px 1200px at 10% 0%, rgba(37,99,235,0.20), transparent 40%), 
                    radial-gradient(1200px 1200px at 90% 0%, rgba(34,197,94,0.18), transparent 40%);
        border: 1px solid var(--border);
        border-radius: 22px;
        box-shadow: var(--shadow);
        padding: 22px 24px;
        overflow: hidden;
      }
      .pf-hero::after {
        content: "";
        position: absolute; inset: 0;
        backdrop-filter: blur(10px);
        border-radius: 22px;
        pointer-events: none;
      }
      .pf-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 18px; }
      @media (max-width: 900px) { .pf-grid { grid-template-columns: repeat(6, 1fr); } }
      @media (max-width: 640px) { .pf-grid { grid-template-columns: repeat(1, 1fr); } }
      .pf-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
        transition: transform 160ms ease, box-shadow 180ms ease, border 160ms ease;
      }
      .pf-card:hover { transform: translateY(-2px); box-shadow: 0 26px 50px rgba(0,0,0,0.30); border-color: rgba(99,102,241,0.25); }
      .pf-balance {
        font-size: 2.2rem; font-weight: 800; letter-spacing: 0.4px;
      }
      .pf-sub { color: var(--text); opacity: 0.75; }
      .pf-tags { display: flex; gap: 10px; flex-wrap: wrap; }
      .pf-tag {
        background: linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0.35));
        color: #0f172a; border: 1px solid var(--border);
        border-radius: 999px; padding: 6px 12px; font-weight: 700; font-size: 0.85rem;
        box-shadow: 0 8px 18px rgba(15,23,42,0.10);
      }
      .pf-kpi { display: flex; justify-content: space-between; align-items: center; }
      .pf-kpi-value { font-size: 1.4rem; font-weight: 800; }
      .pf-kpi-label { font-size: 0.88rem; opacity: 0.75; }
      .pf-timeline { position: relative; padding-left: 18px; }
      .pf-timeline::before { content: ""; position: absolute; left: 8px; top: 6px; bottom: 6px; width: 2px; background: rgba(148,163,184,0.4); border-radius: 2px; }
      .pf-item { position: relative; margin: 8px 0 14px 0; }
      .pf-item::before { content: ""; position: absolute; left: -12px; top: 4px; width: 10px; height: 10px; border-radius: 999px; background: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.20); }
      .pf-cta { display: flex; gap: 12px; align-items: center; }
      .pf-social a { text-decoration: none; margin-right: 12px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='pf-container'>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div class='pf-hero'>", unsafe_allow_html=True)
        cbal, cmeta = st.columns([2.2, 1.2])
        with cbal:
            placeholder = st.empty()
            target = get_cash_balance(user["id"], 500000.0)
            if not st.session_state.get("pf_counter_done"):
                step = max(1, int(target) // 24 if target else 1)
                cur = 0
                import time
                for _ in range(24):
                    cur = min(target, cur + step)
                    placeholder.markdown(f"<div class='pf-balance'>₹{cur:,.0f}</div>", unsafe_allow_html=True)
                    time.sleep(0.03)
                st.session_state["pf_counter_done"] = True
            placeholder.markdown(f"<div class='pf-balance'>₹{target:,.0f}</div>", unsafe_allow_html=True)
            st.caption("Virtual Account Balance")
        with cmeta:
            st.empty()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        symbol = st.text_input("Symbol", "RELIANCE.NS")
    with c2:
        qty = st.number_input("Quantity", min_value=1.0, value=10.0)
    with c3:
        side = st.selectbox("Side", ["BUY", "SELL"])

    if st.button("Execute"):
        price = get_last_price(symbol)
        if price is None:
            st.error("Could not fetch last price.")
        else:
            cash = get_cash_balance(user["id"], 500000.0)
            if side == "BUY":
                cost = float(qty) * float(price)
                if cost > cash:
                    st.error(f"Insufficient balance. Needed ₹{cost:,.2f}, available ₹{cash:,.2f}.")
                else:
                    upsert_portfolio(user["id"], symbol, float(qty), float(price), side)
                    st.success(f"{side} {qty} {symbol} @ ₹{round(price,2)}")
                    st.rerun()
            else:
                held = get_symbol_qty(user["id"], symbol)
                if float(qty) > max(held, 0.0):
                    st.error(f"Insufficient holdings. You have {held} {symbol}.")
                else:
                    upsert_portfolio(user["id"], symbol, float(qty), float(price), side)
                    st.success(f"{side} {qty} {symbol} @ ₹{round(price,2)}")
                    st.rerun()

    rows = get_portfolio(user["id"])
    if rows:
        st.markdown("### Holdings")
        data = []
        total_value = 0.0
        for sym, q, avg in rows:
            lp = get_last_price(sym) or avg
            value = q * lp
            total_value += value
            data.append({"Symbol": sym, "Qty": round(q,2), "Avg Price": round(avg,2), "Last Price": round(lp,2), "Value": round(value,2)})
        st.dataframe(data, use_container_width=True)
        st.metric("Portfolio Value", f"₹{round(total_value,2)}")
        cash = get_cash_balance(user["id"], 500000.0)
        st.metric("Cash Balance", f"₹{cash:,.2f}")
    else:
        st.info("No holdings.")
