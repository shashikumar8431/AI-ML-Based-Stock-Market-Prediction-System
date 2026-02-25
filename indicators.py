import yfinance as yf
import pandas as pd


def fetch_symbol_data(symbol: str, period: str = "6mo", interval: str = "1d"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df is None or df.empty:
        return None
    return df.reset_index()


def compute_rsi(close, period: int = 14):
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    roll_up = up.rolling(period).mean()
    roll_down = down.rolling(period).mean()
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def compute_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def compute_bollinger(close, window=20, num_std=2):
    ma = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return ma, upper, lower


def compute_atr(df: pd.DataFrame, period: int = 14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr


def compute_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low)).fillna(0)
    d = k.rolling(d_period).mean().fillna(0)
    return k, d


def detect_support_resistance(close: pd.Series, window: int = 20):
    sup = close.rolling(window).min()
    res = close.rolling(window).max()
    return sup, res


def get_indicators(symbol: str):
    df = fetch_symbol_data(symbol)
    if df is None or df.empty:
        return None
    close = df["Close"]
    rsi = compute_rsi(close).fillna(0)
    ma20 = close.rolling(window=20).mean().fillna(0)
    macd, macd_sig, macd_hist = compute_macd(close)
    bb_ma, bb_upper, bb_lower = compute_bollinger(close)
    atr = compute_atr(df)
    stoch_k, stoch_d = compute_stochastic(df)
    sup, res = detect_support_resistance(close)
    return {
        "symbol": symbol.upper(),
        "df": df,
        "rsi": rsi,
        "ma20": ma20,
        "macd": macd,
        "macd_signal": macd_sig,
        "macd_hist": macd_hist,
        "bb_ma": bb_ma,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "atr": atr,
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "support": sup,
        "resistance": res,
    }
