import yfinance as yf
import pandas as pd

def get_index_last_price(symbol: str):
    """
    Fetches the latest price and change for a single symbol using fast_info.
    """
    try:
        t = yf.Ticker(symbol)
        # Try fast_info first
        last_price = t.fast_info.get('last_price')
        prev_close = t.fast_info.get('previous_close')

        if last_price and prev_close:
            diff = last_price - prev_close
            pct = (diff / prev_close) * 100
            return {
                "price": round(float(last_price), 2),
                "change": round(float(diff), 2),
                "percent": round(float(pct), 2),
            }
            
        # Fallback to history if fast_info fails
        hist = t.history(period="1d", interval="1m")
        if hist is None or hist.empty:
            return None
            
        last = hist["Close"].iloc[-1]
        
        # Try to get previous close from info or history
        if not prev_close:
            prev_close = t.info.get("previousClose")
            
        if not prev_close:
            hist_long = t.history(period="5d")
            if len(hist_long) >= 2:
                prev_close = hist_long["Close"].iloc[-2]
            else:
                prev_close = hist["Open"].iloc[0]

        diff = last - prev_close
        pct = (diff / prev_close) * 100 if prev_close != 0 else 0
        
        return {
            "price": round(float(last), 2),
            "change": round(float(diff), 2),
            "percent": round(float(pct), 2),
        }
    except Exception:
        return None


def get_live_indices():
    """
    Optimized batch fetch for indices.
    """
    symbols = ["^NSEI", "^NSEBANK", "^BSESN"]
    mapping = {"^NSEI": "nifty", "^NSEBANK": "banknifty", "^BSESN": "sensex"}
    
    results = {
        "nifty": None,
        "banknifty": None,
        "sensex": None
    }
    
    try:
        # Download 2 days to ensure we have yesterday's close for calculation
        # interval='1m' only works for last 7 days, so it's fine.
        # But '1m' data for '2d' might be too much data and slow.
        # Strategy: Get '1d' '1m' for current price, and use 'previousClose' from fast_info/info?
        # yf.download is fast.
        
        # Let's try fetching just the latest data.
        # yfinance download with period="1d", interval="1m" is good for current price.
        # But we need change %.
        
        # Alternative: Use yf.Tickers
        tickers = yf.Tickers(" ".join(symbols))
        
        for sym in symbols:
            try:
                # Accessing .fast_info is much faster than .info
                t = tickers.tickers[sym]
                
                # Current price
                # fast_info['last_price'] is usually available
                last_price = t.fast_info.get('last_price')
                prev_close = t.fast_info.get('previous_close')
                
                if last_price and prev_close:
                    diff = last_price - prev_close
                    pct = (diff / prev_close) * 100
                    
                    results[mapping[sym]] = {
                        "price": round(float(last_price), 2),
                        "change": round(float(diff), 2),
                        "percent": round(float(pct), 2),
                    }
                else:
                    # Fallback to history if fast_info fails
                    hist = t.history(period="1d", interval="1m")
                    if not hist.empty:
                        last = hist["Close"].iloc[-1]
                        # Use first bar as proxy for open if prev_close missing
                        prev = prev_close if prev_close else hist["Open"].iloc[0]
                        diff = last - prev
                        pct = (diff / prev) * 100
                        results[mapping[sym]] = {
                            "price": round(float(last), 2),
                            "change": round(float(diff), 2),
                            "percent": round(float(pct), 2),
                        }
            except Exception:
                continue
                
        return results

    except Exception:
        return results
