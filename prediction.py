import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from backend.predictor import multi_model_predict, backtest_model
from backend.indicators import get_indicators


def render_prediction():
    st.markdown("## 📈 Detailed Stock Prediction")
    
    # Get default symbol from session state if available
    default_sym = st.session_state.get("selected_symbol", "RELIANCE.NS")
    
    symbol = st.text_input("Enter NSE stock symbol", default_sym)
    model = "LR"
    
    # Auto-run if redirected from home (simple heuristic: if symbol matches selected_symbol)
    # We use a session state flag 'prediction_auto_run' to avoid loop
    auto_run = False
    if st.session_state.get("selected_symbol") == symbol and st.session_state.get("prediction_auto_run"):
        auto_run = True
        st.session_state["prediction_auto_run"] = False # Reset flag

    run = st.button("Run Prediction")

    if run or auto_run:
        with st.spinner(f"Predicting for {symbol}..."):
            res = multi_model_predict(symbol, model)
        if res is None:
            st.error("No data found for this symbol.")
        else:
            st.markdown(f"#### {res['symbol']} – Prediction Details")
            c1, c2, c3 = st.columns(3)
            c1.metric("Last Close", f"₹{res['last_close']}")
            c2.metric("Avg Predicted", f"₹{res['avg_future']}")
            as_of_dt = pd.to_datetime(res["df"]["Date"].iloc[-1])
            c2.caption(f"Prediction up to date: {as_of_dt.strftime('%Y-%m-%d')}")
            c3.metric("Signal", res["signal"])
            ind = get_indicators(symbol)
            last_close = float(res["last_close"])
            df_hist = res["df"]
            df_hist["Date"] = pd.to_datetime(df_hist["Date"])
            if isinstance(df_hist.columns, pd.MultiIndex):
                df_hist.columns = [c[0] if isinstance(c, tuple) else c for c in df_hist.columns]
            close_array = pd.to_numeric(np.ravel(np.array(df_hist["Close"])), errors="coerce")
            closes = pd.Series(close_array).dropna()
            tail_trend = closes.tail(15)
            trend_delta = (tail_trend.iloc[-1] - tail_trend.iloc[0]) / max(tail_trend.iloc[0], 1e-9) * 100
            trend = "Uptrend" if trend_delta > 0.5 else ("Downtrend" if trend_delta < -0.5 else "Sideways")
            if ind:
                rsi_src = ind.get("rsi")
                if isinstance(rsi_src, pd.DataFrame):
                    rsi_src = rsi_src.iloc[:, 0]
                rsi_vals = pd.to_numeric(np.ravel(np.array(rsi_src)), errors="coerce") if rsi_src is not None else np.array([])
                rsi_series = pd.Series(rsi_vals).dropna()
                rsi_val = float(rsi_series.iloc[-1]) if len(rsi_series) else 50.0
            else:
                rsi_val = 50.0
            rsi_state = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
            if ind:
                ma_src = ind.get("ma20")
                if isinstance(ma_src, pd.DataFrame):
                    ma_src = ma_src.iloc[:, 0]
                ma_vals = pd.to_numeric(np.ravel(np.array(ma_src)), errors="coerce") if ma_src is not None else np.array([])
                ma_series = pd.Series(ma_vals).dropna()
                ma20_val = float(ma_series.iloc[-1]) if len(ma_series) else last_close
            else:
                ma20_val = last_close
            price_vs_ma = "Above MA20" if last_close > ma20_val else ("Below MA20" if last_close < ma20_val else "At MA20")
            vol_series = closes.tail(30)
            vol_std = float(vol_series.std()) if len(vol_series) > 1 else 0.0
            vol_pct = (vol_std / max(last_close, 1e-9)) * 100
            vol_level = "Low" if vol_pct <= 1.5 else ("Medium" if vol_pct <= 3.0 else "High")
            risk_badge = "🟢 Low Risk" if vol_level == "Low" else ("🟡 Medium Risk" if vol_level == "Medium" else "🔴 High Risk")
            st.markdown(f"**Risk Indicator:** {risk_badge}")
            with st.container(border=True):
                st.markdown("### Why this AI Recommendation?")
                st.markdown(f"- Trend direction: {trend} ({trend_delta:.2f}%)")
                st.markdown(f"- RSI condition: {rsi_state} (RSI {rsi_val:.1f})")
                st.markdown(f"- Price vs Moving Average: {price_vs_ma} (MA20 ₹{ma20_val:.2f})")
                st.markdown(f"- Volatility level: {vol_level} ({vol_pct:.2f}% over last 30 days)")
            df_hist = res["df"]
            df_pred = pd.DataFrame(res["predictions"])
            # Limit historical OHLC to last 60 trading days and ensure datetime (MANDATORY)
            df_hist["Date"] = pd.to_datetime(df_hist["Date"])
            df_hist = df_hist.tail(60)
            df_pred["date"] = pd.to_datetime(df_pred["date"])
            fig = go.Figure()
            # One continuous timeline: historical OHLC + future predictions share the same x-axis
            # Build hovertext since Candlestick does not support hovertemplate
            has_vol = "Volume" in df_hist.columns
            # Ensure numeric types for OHLC/Volume to avoid formatting errors
            if isinstance(df_hist.columns, pd.MultiIndex):
                df_hist.columns = [c[0] if isinstance(c, tuple) else c for c in df_hist.columns]
            dates_arr = df_hist["Date"].to_numpy()
            date_strs = pd.to_datetime(df_hist["Date"]).dt.strftime("%Y-%m-%d").to_numpy()
            open_vals = pd.to_numeric(np.ravel(np.array(df_hist["Open"])), errors="coerce")
            high_vals = pd.to_numeric(np.ravel(np.array(df_hist["High"])), errors="coerce")
            low_vals = pd.to_numeric(np.ravel(np.array(df_hist["Low"])), errors="coerce")
            close_vals = pd.to_numeric(np.ravel(np.array(df_hist["Close"])), errors="coerce")
            if has_vol:
                vol_vals = pd.to_numeric(np.ravel(np.array(df_hist["Volume"])), errors="coerce")
                vol_vals = np.nan_to_num(vol_vals, nan=0).astype(int)
            hovertext = [
                f"Date: {ds}<br>Open: {o:.2f}<br>High: {h:.2f}<br>Low: {l:.2f}<br>Close: {c:.2f}" + (f"<br>Volume: {int(v):,}" if has_vol else "")
                for ds, o, h, l, c, v in zip(
                    date_strs,
                    open_vals,
                    high_vals,
                    low_vals,
                    close_vals,
                    (vol_vals if has_vol else [0]*len(date_strs)),
                )
            ]
            fig.add_trace(go.Candlestick(
                x=dates_arr, open=open_vals, high=high_vals,
                low=low_vals, close=close_vals, name="Historical Price",
                increasing_fillcolor="#22c55e", increasing_line_color="#22c55e",
                decreasing_fillcolor="#ef4444", decreasing_line_color="#ef4444",
                whiskerwidth=0.6, opacity=0.95,
                hovertext=hovertext, hoverinfo="text"
            ))
            open_arr = np.asarray(open_vals, dtype=float)
            close_arr = np.asarray(close_vals, dtype=float)
            high_arr = np.asarray(high_vals, dtype=float)
            low_arr = np.asarray(low_vals, dtype=float)
            body = np.abs(close_arr - open_arr)
            range_arr = np.maximum(high_arr - low_arr, 1e-9)
            doji_idx = np.where(body / range_arr <= 0.1)[0].tolist()
            lower_shadow = np.minimum(open_arr, close_arr) - low_arr
            upper_shadow = high_arr - np.maximum(open_arr, close_arr)
            hammer_idx = np.where((lower_shadow >= 2 * body) & (upper_shadow <= body))[0].tolist()
            star_idx = np.where((upper_shadow >= 2 * body) & (lower_shadow <= body))[0].tolist()
            eng_bull_idx = []
            eng_bear_idx = []
            for i in range(1, len(open_arr)):
                prev_red = close_arr[i-1] < open_arr[i-1]
                curr_green = close_arr[i] > open_arr[i]
                prev_body = np.abs(close_arr[i-1] - open_arr[i-1])
                curr_body = body[i]
                bull = prev_red and curr_green and (curr_body > prev_body) and (open_arr[i] <= close_arr[i-1]) and (close_arr[i] >= open_arr[i-1])
                if bull:
                    eng_bull_idx.append(i)
                prev_green = close_arr[i-1] > open_arr[i-1]
                curr_red = close_arr[i] < open_arr[i]
                bear = prev_green and curr_red and (curr_body > prev_body) and (open_arr[i] >= close_arr[i-1]) and (close_arr[i] <= open_arr[i-1])
                if bear:
                    eng_bear_idx.append(i)
            def pick(lst, n=6):
                return lst[-n:] if len(lst) > n else lst
            doji_idx = pick(doji_idx)
            hammer_idx = pick(hammer_idx)
            star_idx = pick(star_idx)
            eng_bull_idx = pick(eng_bull_idx)
            eng_bear_idx = pick(eng_bear_idx)
            y_range = float(np.nanmax(high_arr) - np.nanmin(low_arr)) if len(high_arr) else 1.0
            padp = y_range * 0.02 if y_range > 0 else 1.0
            if len(doji_idx):
                x = dates_arr[doji_idx]
                y = (high_arr[doji_idx] + padp).astype(float)
                fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", name="Doji", text=["Doji"]*len(x), textposition="top center", marker=dict(color="#64748b", size=8, symbol="diamond")))
            if len(hammer_idx):
                x = dates_arr[hammer_idx]
                y = (high_arr[hammer_idx] + padp).astype(float)
                fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", name="Hammer", text=["Hammer"]*len(x), textposition="top center", marker=dict(color="#22c55e", size=8, symbol="triangle-down")))
            if len(star_idx):
                x = dates_arr[star_idx]
                y = (high_arr[star_idx] + padp).astype(float)
                fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", name="Shooting Star", text=["Star"]*len(x), textposition="top center", marker=dict(color="#f59e0b", size=8, symbol="triangle-up")))
            if len(eng_bull_idx):
                x = dates_arr[eng_bull_idx]
                y = (high_arr[eng_bull_idx] + padp).astype(float)
                fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", name="Bullish Engulfing", text=["Bull"]*len(x), textposition="top center", marker=dict(color="#16a34a", size=9, symbol="circle")))
            if len(eng_bear_idx):
                x = dates_arr[eng_bear_idx]
                y = (high_arr[eng_bear_idx] + padp).astype(float)
                fig.add_trace(go.Scatter(x=x, y=y, mode="markers+text", name="Bearish Engulfing", text=["Bear"]*len(x), textposition="top center", marker=dict(color="#dc2626", size=9, symbol="circle-open")))
            # Make prediction continue from the last historical close (connector point for smooth transition)
            last_hist_date = df_hist["Date"].iloc[-1]
            last_hist_close = float(close_vals[-1])
            pred_dates = np.concatenate(([last_hist_date], df_pred["date"].to_numpy()))
            pred_prices = np.concatenate(([last_hist_close], df_pred["price"].astype(float).to_numpy()))
            # Color per signal for professional clarity
            signal_color = {"SELL": "red", "BUY": "green", "HOLD": "orange"}.get(res["signal"], "blue")
            fig.add_trace(go.Scatter(
                x=pred_dates, y=pred_prices, mode="lines+markers",
                name=f"AI Prediction • up to date {as_of_dt.strftime('%Y-%m-%d')}", line=dict(color=signal_color, width=3)
            ))
            # Confidence band using recent volatility (shaded, non-intrusive)
            vol = float(np.std(df_hist["Close"].tail(30))) if len(df_hist) >= 30 else float(np.std(df_hist["Close"]))
            upper = df_pred["price"].astype(float).to_numpy() + vol
            lower = df_pred["price"].astype(float).to_numpy() - vol
            fig.add_trace(go.Scatter(x=df_pred["date"], y=upper, line=dict(color="rgba(0,0,255,0.25)", width=0), name="Upper Bound", showlegend=False))
            fig.add_trace(go.Scatter(x=df_pred["date"], y=lower, fill="tonexty", fillcolor="rgba(0,0,255,0.2)", line=dict(color="rgba(0,0,255,0.25)", width=0), name="Lower Bound", showlegend=False))
            # Reference lines tied to unified y-axis; do not drive autoscale
            fig.add_hline(y=res["last_close"], line_dash="dot", line_color="red", annotation_text="Last Close", annotation_position="top left")
            support = float(np.nanmin(low_vals))
            resistance = float(np.nanmax(high_vals))
            # Axis range: use recent historical + predicted prices + last close (do NOT include support/resistance to avoid distortion)
            min_date = df_hist["Date"].min()                    # start of 60-day window
            max_date = df_pred["date"].max()                    # end at last prediction date
            y_candidates = [
                float(df_hist["Low"].min()),                    # recent historical lows
                float(df_hist["High"].max()),                   # recent historical highs
                float(df_pred["price"].astype(float).min()),    # predicted min
                float(df_pred["price"].astype(float).max()),    # predicted max
                float(res["last_close"]),                       # last close reference
            ]
            y_min = float(np.min(y_candidates))
            y_max = float(np.max(y_candidates))
            pad = (y_max - y_min) * 0.03 if (y_max - y_min) > 0 else 1.0
            fig.update_xaxes(
                range=[min_date, max_date],
                showgrid=True, gridcolor="#e5e7eb", gridwidth=1,
                showline=True, linecolor="#cbd5e1", linewidth=1,
                rangeslider_visible=False,
                rangeselector=dict(
                    buttons=[
                        dict(count=7, label="1W", step="day", stepmode="backward"),
                        dict(count=14, label="2W", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(step="all", label="All"),
                    ]
                ),
            )
            fig.update_yaxes(
                range=[y_min - pad, y_max + pad], fixedrange=False,
                showgrid=True, gridcolor="#e5e7eb", gridwidth=1,
                showline=True, linecolor="#cbd5e1", linewidth=1
            )
            # Keep support/resistance visible but clamped inside visible range (do not alter y-range)
            sup_clamped = max(y_min - pad, min(support, y_max + pad))
            res_clamped = max(y_min - pad, min(resistance, y_max + pad))
            fig.add_hline(y=sup_clamped, line_dash="dash", line_color="green", annotation_text="Support")
            fig.add_hline(y=res_clamped, line_dash="dash", line_color="orange", annotation_text="Resistance")
            # Professional chart layout: white template, unified hover, clear legend
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price",
                height=620,
                xaxis_rangeslider_visible=False,
                template="plotly_white",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig, width="stretch")
            with st.container(border=True):
                st.markdown("⚠️ This system is for educational purposes only and does not provide financial advice.")
            st.caption("This project aligns with UN SDG 8 – Decent Work and Economic Growth by promoting financial literacy and informed decision-making.")
            bt = backtest_model(res["symbol"])
            if bt:
                dates = pd.to_datetime(bt["dates"])
                date_strs = pd.Series(dates).dt.strftime("%Y-%m-%d")
                actual = np.asarray(bt["actual"], dtype=float).ravel()
                predicted = np.asarray(bt["predicted"], dtype=float).ravel()
                fig_bt = go.Figure()
                fig_bt.add_trace(go.Scatter(x=date_strs, y=actual, name="Actual", mode="lines+markers", line=dict(color="#0f172a"), connectgaps=True))
                fig_bt.add_trace(go.Scatter(x=date_strs, y=predicted, name="Predicted", mode="lines+markers", line=dict(color="#60a5fa"), connectgaps=True))
                y_min = float(np.nanmin([actual.min(), predicted.min()]))
                y_max = float(np.nanmax([actual.max(), predicted.max()]))
                pad_bt = (y_max - y_min) * 0.05 if (y_max - y_min) > 0 else 1.0
                fig_bt.update_yaxes(range=[y_min - pad_bt, y_max + pad_bt], showgrid=True, gridcolor="#e5e7eb")
                fig_bt.update_xaxes(showgrid=True, gridcolor="#e5e7eb")
                fig_bt.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Price",
                    template="plotly_white",
                    hovermode="x unified",
                    height=380,
                    margin=dict(l=10, r=10, t=40, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_bt, width="stretch")

    try:
        import yfinance as yf
        df_live = yf.download(symbol, period="5d", interval="30m", progress=False)
        if df_live is not None and not df_live.empty:
            df_live = df_live.reset_index()
            candle = go.Figure()
            candle.add_trace(go.Candlestick(x=df_live["Datetime"], open=df_live["Open"], high=df_live["High"], low=df_live["Low"], close=df_live["Close"], name="OHLC"))
            candle.add_trace(go.Bar(x=df_live["Datetime"], y=df_live["Volume"], name="Volume", marker_color="rgba(99, 110, 250, 0.5)", yaxis="y2"))
            candle.update_layout(xaxis_rangeslider_visible=False, yaxis_domain=[0.25, 1.0], yaxis2_domain=[0.0, 0.2], height=500, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(candle, use_container_width=True)
    except Exception:
        pass
