import streamlit as st

from backend.db import add_watchlist_item, get_watchlist
from backend.predictor import train_and_predict
from auth import session


def render_watchlist():
    # Watchlist page content: show user's watchlist and quick predictions
    session.ensure_session()
    user = session.current_user()

    st.markdown("## ⭐ Watchlist")
    if user is None:
        st.warning("Please login to access your watchlist.")
        return

    st.markdown(f"Logged in as **{user['email']}**")

    sym = st.text_input("Symbol to add (e.g., SBIN.NS)", "SBIN.NS")
    if st.button("Add to Watchlist"):
        add_watchlist_item(user["id"], sym)
        st.success(f"Added {sym.upper()} to watchlist.")

    symbols = get_watchlist(user["id"])
    if not symbols:
        st.info("Your watchlist is empty.")
    else:
        st.markdown("### Your Watchlist")
        for s in symbols:
            st.markdown(f"#### {s}")
            res = train_and_predict(s)
            if res is None:
                st.write("No data or error fetching this symbol.")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Last Close", f"₹{res['last_close']}")
                c2.metric("Avg Predicted", f"₹{res['avg_future']}")
                c3.metric("Signal", res["signal"])

