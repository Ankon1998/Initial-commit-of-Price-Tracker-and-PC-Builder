import time
from database import init_db, get_all_products, log_price
from scraper import search_and_get_price, STORES

def background_sync():
    init_db()
    print("Background Tracker Started...")
    while True:
        products = get_all_products()
        for p_id, p_name, p_query, p_target in products:
            print(f"Syncing {p_name}...")
            # Check price only in Startech (or all) for history
            price = search_and_get_price(p_query, "startech")
            if price:
                log_price(p_id, price)
                print(f"Logged: {price} Tk")
        
        print("Waiting 1 hour for next sync...")
        time.sleep(3600)

if __name__ == "__main__":
    background_sync()