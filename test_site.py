import sqlite3

conn = sqlite3.connect("tracker.db")
cursor = conn.cursor()

# Delete everything to start fresh
cursor.execute("DELETE FROM products")
cursor.execute("DELETE FROM price_history")

# Add ONLY the working laptop
working_url = "https://www.startech.com.bd/hp-15s-du3528tu-core-i3-11th-gen-laptop"
cursor.execute("INSERT INTO products (name, url, target_price) VALUES (?, ?, ?)", 
               ("HP Laptop", working_url, 45000.0))

conn.commit()
conn.close()
print("Database cleaned! Only one working product remains.")