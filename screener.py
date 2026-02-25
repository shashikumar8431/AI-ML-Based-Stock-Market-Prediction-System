import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from backend.indicators import get_indicators


DEFAULT_SYMBOLS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","AXISBANK.NS",
    "HINDUNILVR.NS","KOTAKBANK.NS","ASIANPAINT.NS","MARUTI.NS","WIPRO.NS","ULTRACEMCO.NS","SUNPHARMA.NS","ONGC.NS","NTPC.NS","TITAN.NS"
]


def fetch_quote(sym: str):
    try:
        t = yf.Ticker(sym)
        hist = t.history(period="2d")
        if hist is None or hist.empty:
            return None
        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
        diff = last - prev
        pct = (diff / prev * 100.0) if prev else 0.0
        vol = int(hist["Volume"].iloc[-1])
        return {"price": round(last,2), "pct": round(pct,2), "volume": vol}
    except Exception:
        return None


def render_screener():
    st.markdown("## 🟦 Market Screener")
    symbols = st.text_area("Symbols (comma-separated)", ",".join(DEFAULT_SYMBOLS))
    syms = [s.strip() for s in symbols.split(",") if s.strip()]
    sort_by = st.selectbox("Sort by", ["AI Score","Change %","RSI","Price","Volume"], index=0)
    limit = st.number_input("Max symbols", min_value=5, max_value=50, value=20, step=5)
    rows = []
    prog = st.progress(0)
    total = min(len(syms), int(limit))
    def _series(x):
        if isinstance(x, pd.DataFrame):
            x = x.iloc[:, 0]
        elif isinstance(x, (list, tuple, np.ndarray)):
            x = pd.Series(x)
        elif not isinstance(x, pd.Series):
            x = pd.Series([x])
        return pd.to_numeric(x, errors="coerce")
    def last_float(x):
        s = _series(x).dropna()
        return float(s.iloc[-1]) if len(s) else 0.0
    for i, s in enumerate(syms[:total], start=1):
        quote = fetch_quote(s)
        ind = get_indicators(s)
        if quote and ind:
            rsi = last_float(ind["rsi"])
            ma20 = last_float(ind["ma20"])
            macd = last_float(ind["macd"])
            macd_sig = last_float(ind["macd_signal"])
            stoch_k = last_float(ind["stoch_k"])
            price = quote["price"]
            score = 0
            score += 1 if rsi < 30 else (-1 if rsi > 70 else 0)
            score += 1 if macd > macd_sig else (-1 if macd < macd_sig else 0)
            score += 1 if stoch_k < 20 else (-1 if stoch_k > 80 else 0)
            score += 1 if price > ma20 else (-1 if price < ma20 else 0)
            final = "BUY" if score >= 2 else ("SELL" if score <= -2 else "HOLD")
            rows.append({
                "Symbol": s,
                "Price": price,
                "Change %": quote["pct"],
                "Volume": quote["volume"],
                "RSI": round(rsi,2),
                "MA20": round(ma20,2),
                "MACD": round(macd,2),
                "Stoch %K": round(stoch_k,2),
                "AI Score": int(score),
                "Signal": final,
            })
        prog.progress(min(i/total,1.0))
    df = pd.DataFrame(rows)
    if not df.empty:
        if sort_by in df.columns:
            df = df.sort_values(by=sort_by, ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data available.")
