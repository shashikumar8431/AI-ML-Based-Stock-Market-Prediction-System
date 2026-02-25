import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "ai_stock.db")


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            qty REAL NOT NULL,
            avg_price REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            qty REAL NOT NULL,
            price REAL NOT NULL,
            side TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            type TEXT NOT NULL,
            threshold REAL NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        '''
    )
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS search_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(name: str, email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password)),
        )
        conn.commit()
        return True, "Registration successful."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, email FROM users WHERE email = ? AND password_hash = ?",
        (email, hash_password(password)),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "email": row[2]}
    return None


def get_user_stats(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    stats = {}
    
    # Watchlist count
    cur.execute("SELECT COUNT(*) FROM watchlist WHERE user_id = ?", (user_id,))
    stats["watchlist_count"] = cur.fetchone()[0]
    
    # Portfolio count
    cur.execute("SELECT COUNT(*) FROM portfolio WHERE user_id = ?", (user_id,))
    stats["portfolio_count"] = cur.fetchone()[0]
    
    # Search history count
    cur.execute("SELECT COUNT(*) FROM search_log WHERE user_id = ?", (user_id,))
    stats["search_count"] = cur.fetchone()[0]
    
    conn.close()
    return stats


def add_watchlist_item(user_id: int, symbol: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO watchlist (user_id, symbol) VALUES (?, ?)",
        (user_id, symbol.upper()),
    )
    conn.commit()
    conn.close()


def get_watchlist(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT symbol FROM watchlist WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def log_search(user_id: int | None, symbol: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO search_log (user_id, symbol) VALUES (?, ?)", (user_id, symbol))
    conn.commit()
    conn.close()


def get_user_searches(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT symbol, ts FROM search_log WHERE user_id = ? ORDER BY ts DESC LIMIT 50", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def upsert_portfolio(user_id: int, symbol: str, qty_delta: float, price: float, side: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT qty, avg_price FROM portfolio WHERE user_id = ? AND symbol = ?", (user_id, symbol))
    row = cur.fetchone()
    if row:
        qty, avg_price = row
        if side == "BUY":
            new_qty = qty + qty_delta
            new_avg = (qty * avg_price + qty_delta * price) / max(new_qty, 1e-9)
        else:
            new_qty = qty - qty_delta
            new_avg = avg_price
        cur.execute("UPDATE portfolio SET qty = ?, avg_price = ? WHERE user_id = ? AND symbol = ?", (new_qty, new_avg, user_id, symbol))
    else:
        cur.execute("INSERT INTO portfolio (user_id, symbol, qty, avg_price) VALUES (?, ?, ?, ?)", (user_id, symbol, qty_delta if side == "BUY" else -qty_delta, price))
    cur.execute("INSERT INTO transactions (user_id, symbol, qty, price, side) VALUES (?, ?, ?, ?, ?)", (user_id, symbol, qty_delta, price, side))
    conn.commit()
    conn.close()


def get_portfolio(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT symbol, qty, avg_price FROM portfolio WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_cash_balance(user_id: int, starting: float = 500000.0) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT side, qty, price FROM transactions WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    cash = float(starting)
    for side, qty, price in rows:
        amt = float(qty) * float(price)
        if str(side).upper() == "BUY":
            cash -= amt
        else:
            cash += amt
    return round(cash, 2)


def get_symbol_qty(user_id: int, symbol: str) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT qty FROM portfolio WHERE user_id = ? AND symbol = ?", (user_id, symbol))
    row = cur.fetchone()
    conn.close()
    return float(row[0]) if row else 0.0


def reset_password(email: str, new_password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "Email not found."
    cur.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hash_password(new_password), email))
    conn.commit()
    conn.close()
    return True, "Password updated. Please log in."


def update_user_name(user_id: int, name: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    conn.close()
    return True


def change_password(user_id: int, current_password: str, new_password: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "User not found."
    if row[0] != hash_password(current_password):
        conn.close()
        return False, "Current password incorrect."
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
    conn.commit()
    conn.close()
    return True, "Password changed."
