import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from datetime import timedelta
import streamlit as st


def fetch_history(symbol: str, period: str = "1y", interval: str = "1d"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df is None or df.empty:
        return None
    df = df.reset_index()
    # Normalize date column to 'Date'
    if "Date" not in df.columns:
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        elif "index" in df.columns and pd.api.types.is_datetime64_any_dtype(df["index"]):
            df = df.rename(columns={"index": "Date"})
        else:
            # Fallback: create Date from index if possible
            if isinstance(df.index, pd.DatetimeIndex):
                df["Date"] = df.index
            else:
                # Try to find any datetime-like column
                dt_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
                if dt_cols:
                    df = df.rename(columns={dt_cols[0]: "Date"})
                else:
                    df["Date"] = pd.to_datetime(df.index)
    return df


def prepare_data(df: pd.DataFrame):
    df["Date_ordinal"] = pd.to_datetime(df["Date"]).map(pd.Timestamp.toordinal)
    X = df[["Date_ordinal"]].values.reshape(-1, 1)
    y = df["Close"].values
    return X, y, df


def train_and_predict(symbol: str):
    df = fetch_history(symbol)
    if df is None or df.empty:
        return None
    X, y, dfp = prepare_data(df)
    model = LinearRegression()
    model.fit(X, y)

    last_date = pd.to_datetime(dfp["Date"].iloc[-1])
    future_dates = [last_date + timedelta(days=i) for i in range(1, 8)]
    future_ord = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    preds = model.predict(future_ord)
    preds = np.asarray(preds).ravel()
    volatility = np.std(y[-30:]) if len(y) >= 30 else np.std(y)
    noise = np.random.normal(0, volatility * 0.2, size=len(preds))
    preds = preds + noise

    last_close = float(np.asarray(dfp["Close"].iloc[-1]).item())
    avg_future = float(np.mean(preds))

    if avg_future > last_close * 1.01:
        signal = "BUY"
    elif avg_future < last_close * 0.99:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "symbol": symbol.upper(),
        "df": dfp.tail(60),
        "last_close": round(last_close, 2),
        "avg_future": round(avg_future, 2),
        "signal": signal,
        "confidence": round(max(60, 100 - (volatility / last_close) * 100), 2) if last_close else 60.0,
        "predictions": [
            {"date": d.strftime("%Y-%m-%d"), "price": round(float(p), 2)}
            for d, p in zip(future_dates, preds)
        ],
    }


def train_and_predict_rf(symbol: str):
    df = fetch_history(symbol)
    if df is None or df.empty:
        return None
    X, y, dfp = prepare_data(df)
    model = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y)

    last_date = pd.to_datetime(dfp["Date"].iloc[-1])
    future_dates = [last_date + timedelta(days=i) for i in range(1, 8)]
    future_ord = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    preds = model.predict(future_ord)

    last_close = float(dfp["Close"].iloc[-1])
    avg_future = float(np.mean(preds))

    signal = "BUY" if avg_future > last_close * 1.01 else ("SELL" if avg_future < last_close * 0.99 else "HOLD")
    return {
        "symbol": symbol.upper(),
        "last_close": round(last_close, 2),
        "avg_future": round(avg_future, 2),
        "signal": signal,
        "predictions": [
            {"date": d.strftime("%Y-%m-%d"), "price": round(float(p), 2)}
            for d, p in zip(future_dates, preds)
        ],
    }


def confidence_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        return 50.0
    err = np.abs(y_true - y_pred)
    mae = float(np.mean(err))
    denom = float(np.mean(np.abs(y_true))) or 1.0
    conf = max(0.0, 100.0 - (mae / denom) * 100.0)
    return round(conf, 2)


def multi_model_predict(symbol: str, model_name: str = "LR"):
    df = fetch_history(symbol)
    if df is None or df.empty:
        return None
    X, y, dfp = prepare_data(df)
    last_date = pd.to_datetime(dfp["Date"].iloc[-1])
    future_dates = [last_date + timedelta(days=i) for i in range(1, 8)]
    future_ord = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)

    if model_name == "RF":
        model = RandomForestRegressor(n_estimators=200, random_state=42).fit(X, y)
    else:
        model = LinearRegression().fit(X, y)

    preds = model.predict(future_ord)
    preds = np.asarray(preds).ravel()
    last_close = float(np.asarray(dfp["Close"].iloc[-1]).item())
    avg_future = float(np.mean(preds))
    signal = "BUY" if avg_future > last_close * 1.01 else ("SELL" if avg_future < last_close * 0.99 else "HOLD")

    recent_true = y[-30:] if len(y) >= 30 else y
    recent_X = X[-len(recent_true):]
    recent_pred = model.predict(recent_X)
    conf = confidence_score(recent_true, recent_pred)

    return {
        "symbol": symbol.upper(),
        "df": dfp.tail(60),
        "last_close": round(last_close, 2),
        "avg_future": round(avg_future, 2),
        "signal": signal,
        "confidence": conf,
        "predictions": [
            {"date": d.strftime("%Y-%m-%d"), "price": round(float(p), 2)}
            for d, p in zip(future_dates, preds)
        ],
    }

@st.cache_data(ttl=3600)
def get_featured_predictions(symbols=None):
    if symbols is None:
        symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"]
    results = []
    for sym in symbols:
        try:
            res = train_and_predict(sym)
            if res:
                results.append(res)
        except Exception:
            continue
    return results


def backtest_model(symbol: str):
    df = fetch_history(symbol, period="6mo")
    if df is None or len(df) < 60:
        return None
    X, y, dfp = prepare_data(df)
    train_X, test_X = X[:-7], X[-7:]
    train_y, test_y = y[:-7], y[-7:]
    model = LinearRegression()
    model.fit(train_X, train_y)
    preds = model.predict(test_X)
    return {
        "dates": dfp["Date"].tail(7),
        "actual": test_y,
        "predicted": preds,
    }
