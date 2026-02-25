import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Expanded sector map with major NIFTY 50 stocks
SECTOR_MAP = {
    # Banking & Finance
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "AXISBANK.NS": "Banking",
    "KOTAKBANK.NS": "Banking",
    "INDUSINDBK.NS": "Banking",
    "BAJFINANCE.NS": "Finance",
    "BAJAJFINSV.NS": "Finance",
    
    # IT
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HCLTECH.NS": "IT",
    "WIPRO.NS": "IT",
    "TECHM.NS": "IT",
    
    # Energy & Oil
    "RELIANCE.NS": "Energy",
    "ONGC.NS": "Energy",
    "NTPC.NS": "Energy",
    "POWERGRID.NS": "Energy",
    "BPCL.NS": "Energy",
    "IOC.NS": "Energy",
    
    # FMCG
    "ITC.NS": "FMCG",
    "HINDUNILVR.NS": "FMCG",
    "NESTLEIND.NS": "FMCG",
    "BRITANNIA.NS": "FMCG",
    "TATACONSUM.NS": "FMCG",
    
    # Auto
    "MARUTI.NS": "Auto",
    "M&M.NS": "Auto",
    "TATAMOTORS.NS": "Auto",
    "BAJAJ-AUTO.NS": "Auto",
    "EICHERMOT.NS": "Auto",
    "HEROMOTOCO.NS": "Auto",
    
    # Pharma
    "SUNPHARMA.NS": "Pharma",
    "DRREDDY.NS": "Pharma",
    "CIPLA.NS": "Pharma",
    "DIVISLAB.NS": "Pharma",
    "APOLLOHOSP.NS": "Pharma",
    
    # Metals
    "TATASTEEL.NS": "Metals",
    "HINDALCO.NS": "Metals",
    "JSWSTEEL.NS": "Metals",
    "COALINDIA.NS": "Metals",
    
    # Others
    "LT.NS": "Infra",
    "BHARTIARTL.NS": "Telecom",
    "ASIANPAINT.NS": "Consumer",
    "TITAN.NS": "Consumer",
    "ULTRACEMCO.NS": "Cement",
    "ADANIENT.NS": "Adani Group",
    "ADANIPORTS.NS": "Adani Group",
}

def fetch_heatmap_data():
    symbols = list(SECTOR_MAP.keys())
    # Batch fetch for speed
    try:
        # Fetch 2 days to calculate change
        df = yf.download(symbols, period="2d", progress=False, group_by='ticker')
        
        data = []
        for sym in symbols:
            try:
                # Handle MultiIndex or Single Index depending on result structure
                # yf.download with group_by='ticker' returns a DF where top level columns are Tickers
                if sym not in df.columns:
                    continue
                    
                hist = df[sym]
                if hist.empty or len(hist) < 1:
                    continue
                
                # Get last two rows for change calc
                # If only 1 row (e.g. market just opened or data issue), change is 0
                if len(hist) >= 2:
                    prev = float(hist["Close"].iloc[-2])
                    last = float(hist["Close"].iloc[-1])
                    pct = ((last - prev) / prev) * 100.0 if prev != 0 else 0.0
                else:
                    last = float(hist["Close"].iloc[-1])
                    pct = 0.0
                
                # Use Volume as a proxy for 'Size' (or just 1 for equal size)
                # We'll use Volume to give bigger stocks (more activity) more space
                vol = float(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 1.0
                
                data.append({
                    "Symbol": sym,
                    "Sector": SECTOR_MAP[sym],
                    "Price": round(last, 2),
                    "%Change": round(pct, 2),
                    "Volume": vol
                })
            except Exception:
                continue
                
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def render_heatmap():
    st.markdown("## 🗺 Market Heatmap (NIFTY 50 Focus)")
    st.caption("Size represents Volume, Color represents % Change")
    
    if st.button("Refresh Data"):
        st.rerun()

    with st.spinner("Fetching market data..."):
        df = fetch_heatmap_data()
    
    if df.empty:
        st.warning("No data available. Please check your internet connection.")
        return

    # Create the treemap
    # color_continuous_midpoint=0 ensures 0 is the center (white/neutral)
    fig = px.treemap(
        df,
        path=[px.Constant("NIFTY 50"), "Sector", "Symbol"],
        values="Volume",
        color="%Change",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        hover_data=["Price", "%Change", "Volume"],
        custom_data=["Price", "%Change"]
    )
    
    # Update layout to make it look professional
    fig.update_traces(
        textposition="middle center",
        texttemplate="%{label}<br>%{customdata[0]}<br>%{customdata[1]}%",
        textfont_size=14
    )
    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)
