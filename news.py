import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Expanded dictionary for better sentiment accuracy on financial headlines
POS_WORDS = {
    "gain", "up", "surge", "positive", "beat", "strong", "rally", "bullish", 
    "growth", "profit", "jump", "rise", "high", "record", "buy", "outperform", 
    "upgrade", "soar", "climb", "success", "deal", "partnership", "launch",
    "win", "dividend", "bonus", "acquisition", "merger", "green"
}
NEG_WORDS = {
    "loss", "down", "drop", "negative", "miss", "weak", "fall", "bearish", 
    "decline", "crash", "slump", "low", "sell", "underperform", "downgrade", 
    "plunge", "fail", "lawsuit", "scandal", "fraud", "risk", "debt", 
    "bankruptcy", "concern", "warning", "ban", "penalty", "fine"
}

def score_sentiment(text: str) -> tuple[int, str]:
    """
    Returns a tuple (score, label)
    Score > 0: Positive
    Score < 0: Negative
    Score = 0: Neutral
    """
    if not text:
        return 0, "Neutral"
        
    t = text.lower()
    # Simple tokenization by splitting on non-alphanumeric
    words = set("".join(c if c.isalnum() else " " for c in t).split())
    
    pos_score = sum(1 for w in POS_WORDS if w in words)
    neg_score = sum(1 for w in NEG_WORDS if w in words)
    
    score = pos_score - neg_score
    
    if score > 0:
        return score, "Positive"
    elif score < 0:
        return score, "Negative"
    else:
        return 0, "Neutral"

def parse_news_item(item):
    """
    Parses a news item from yfinance, handling different response structures.
    Returns: (title, link, publisher, time_str, thumbnail_url)
    """
    try:
        # Check for new structure (nested in 'content')
        if "content" in item and isinstance(item["content"], dict):
            c = item["content"]
            title = c.get("title", "")
            
            # Link
            link = c.get("clickThroughUrl", {}).get("url", "")
            if not link:
                link = c.get("canonicalUrl", {}).get("url", "")
                
            # Publisher
            provider = c.get("provider", {}).get("displayName", "Unknown")
            
            # Time
            pubDate = c.get("pubDate", "") # ISO string like '2025-12-30T02:03:46Z'
            if pubDate:
                try:
                    # Parse ISO format
                    dt = datetime.strptime(pubDate.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                    time_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    time_str = pubDate.replace("T", " ").replace("Z", "")
            else:
                time_str = ""
            
            # Thumbnail
            thumb_obj = c.get("thumbnail", {})
            thumbnail = ""
            if thumb_obj and "resolutions" in thumb_obj and thumb_obj["resolutions"]:
                thumbnail = thumb_obj["resolutions"][0].get("url", "")
                
            return title, link, provider, time_str, thumbnail
            
        else:
            # Old structure (flat)
            title = item.get("title", "")
            link = item.get("link", "")
            provider = item.get("publisher", "")
            
            ts = item.get("providerPublishTime", 0)
            if ts:
                try:
                    time_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                except:
                    time_str = ""
            else:
                time_str = ""
                
            thumb_obj = item.get("thumbnail", {})
            thumbnail = ""
            if thumb_obj and "resolutions" in thumb_obj and thumb_obj["resolutions"]:
                thumbnail = thumb_obj["resolutions"][0].get("url", "")
                
            return title, link, provider, time_str, thumbnail
            
    except Exception:
        return "", "", "", "", ""

def render_news():
    st.markdown("## 📰 Market News & Sentiment")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input("Enter stock symbol (e.g., RELIANCE.NS, ^NSEI for Market)", "RELIANCE.NS")
    with col2:
        filter_opt = st.selectbox("Filter Sentiment", ["All", "Positive", "Negative", "Neutral"])

    if st.button("Fetch News"):
        with st.spinner(f"Fetching news for {symbol}..."):
            try:
                t = yf.Ticker(symbol)
                news = getattr(t, "news", [])
                
                if not news:
                    st.info("No news found for this symbol. Try a major index like ^NSEI.")
                    return

                # Process and filter news
                processed_news = []
                for item in news:
                    title, link, publisher, time_str, thumbnail = parse_news_item(item)
                    
                    if not title:
                        continue
                        
                    score, sentiment = score_sentiment(title)
                    
                    if filter_opt != "All" and sentiment != filter_opt:
                        continue
                        
                    processed_news.append({
                        "title": title,
                        "link": link,
                        "publisher": publisher,
                        "time": time_str,
                        "thumbnail": thumbnail,
                        "sentiment": sentiment,
                        "score": score
                    })

                st.markdown(f"### Latest Stories for {symbol.upper()}")
                
                if not processed_news:
                    st.warning(f"No news found matching filter: {filter_opt}")
                    return

                for item in processed_news:
                    # Card-like layout
                    with st.container():
                        # Sentiment Badge Color
                        badge_color = "#94a3b8" # Gray/Neutral
                        if item["sentiment"] == "Positive":
                            badge_color = "#22c55e" # Green
                        elif item["sentiment"] == "Negative":
                            badge_color = "#ef4444" # Red
                            
                        # Layout: Image (if any) + Content
                        c1, c2 = st.columns([1, 4])
                        
                        with c1:
                            if item["thumbnail"]:
                                st.image(item["thumbnail"], use_container_width=True)
                            else:
                                # Placeholder icon
                                st.markdown(
                                    """
                                    <div style="
                                        display: flex; 
                                        justify-content: center; 
                                        align-items: center; 
                                        height: 80px; 
                                        background-color: #1e293b; 
                                        border-radius: 8px;
                                    ">
                                        <span style="font-size: 24px;">📰</span>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )

                        with c2:
                            # Link handling
                            if item['link']:
                                st.markdown(f"#### [{item['title']}]({item['link']})")
                            else:
                                st.markdown(f"#### {item['title']}")
                                
                            st.caption(f"{item['publisher']} • {item['time']}")
                            
                            # Badge
                            st.markdown(
                                f"""
                                <span style="
                                    background-color: {badge_color}20;
                                    color: {badge_color};
                                    padding: 2px 8px;
                                    border-radius: 4px;
                                    font-size: 12px;
                                    font-weight: 600;
                                    border: 1px solid {badge_color}40;
                                ">
                                    {item['sentiment']}
                                </span>
                                """, 
                                unsafe_allow_html=True
                            )
                        
                        st.markdown("---")
                        
            except Exception as e:
                st.error(f"Error fetching news: {e}")
