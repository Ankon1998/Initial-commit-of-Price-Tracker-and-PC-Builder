import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    
    # Table for shop configurations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            search_url TEXT,
            price_tag TEXT
        )
    """)
    
    # NEW: Table for search analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Pre-defined shop data to save you work
    initial_shops = [
        ("startech", "https://www.startech.com.bd/product/search?search=", "ins, .p-item-price, .price, .price-new"),
        ("techland", "https://www.techlandbd.com/search/advance/product/result/?search=", "span.text-red-600.font-bold, .price-new, .price"),
        ("ryans", "https://www.ryanscomputers.com/search?q=", "p.pr-text.cat-sp-text, .p-item-price, .price")
    ]
    
    for name, url, tag in initial_shops:
        cursor.execute("INSERT OR IGNORE INTO shops (name, search_url, price_tag) VALUES (?, ?, ?)", (name, url, tag))
    
    conn.commit()
    conn.close()

def log_search(query):
    """Records every search query performed by users"""
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO search_logs (query) VALUES (?)", (query,))
    conn.commit()
    conn.close()

def get_search_stats():
    """Retrieves the top 5 trending products for admin analytics"""
    conn = sqlite3.connect("tracker.db")
    df = pd.read_sql_query("""
        SELECT query, COUNT(*) as count 
        FROM search_logs 
        GROUP BY query 
        ORDER BY count DESC 
        LIMIT 5
    """, conn)
    conn.close()
    return df

def get_shops():
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, search_url, price_tag FROM shops")
    shops = {row[0]: {"search_url": row[1], "price_tag": row[2]} for row in cursor.fetchall()}
    conn.close()
    return shops

def add_shop(name, url, tag):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO shops (name, search_url, price_tag) VALUES (?, ?, ?)", (name, url, tag))
    conn.commit()
    conn.close()

def delete_shop(name):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM shops WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def update_shop(old_name, new_name, new_url, new_tag):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE shops SET name=?, search_url=?, price_tag=? WHERE name=?", (new_name, new_url, new_tag, old_name))
    conn.commit()
    conn.close()