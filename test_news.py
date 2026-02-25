import yfinance as yf
try:
    t = yf.Ticker("RELIANCE.NS")
    news = t.news
    print(f"News count: {len(news)}")
    if news:
        print(f"First item keys: {news[0].keys()}")
        print(f"First item: {news[0]}")
except Exception as e:
    print(f"Error: {e}")
