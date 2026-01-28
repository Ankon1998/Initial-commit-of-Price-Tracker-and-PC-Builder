from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time

def search_and_get_price(query, store_name, store_config):
    """
    The main engine that scrapes prices and images from tech stores.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Runs in background
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    # Modern User-Agent to prevent bot detection
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    search_base = store_config['search_url']
    price_tag = store_config['price_tag']

    # Handle direct URLs or search terms
    if query.startswith("http"):
        final_url = query
    else:
        final_url = f"{search_base}{query.replace(' ', '%20')}"

    try:
        driver.get(final_url)
        # Wait for dynamic content (scripts/stock checks)
        time.sleep(2) 
        
        wait = WebDriverWait(driver, 10)
        # Find the price element using the CSS selector from DB
        price_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, price_tag)))
        
        # 1. Price Extraction
        raw_text = price_element.text.replace(",", "")
        match = re.search(r'\d+', raw_text)
        price = float(match.group()) if match else None

        # 2. Link Extraction
        try:
            link_element = price_element.find_element(By.XPATH, "./ancestor::a")
            product_url = link_element.get_attribute("href")
        except:
            product_url = driver.current_url

        # 3. Image Extraction with Mirroring Logic
        img_url = None
        try:
            parent = price_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'card') or contains(@class, 'product') or contains(@class, 'item') or contains(@class, 'p-item')]")
            img_tag = parent.find_element(By.TAG_NAME, "img")
            
            # Check data-src for lazy-loading
            img_url = img_tag.get_attribute("data-src") or img_tag.get_attribute("src")

            # Techland ID Reconstruction fix
            if "techlandbd.com" in product_url:
                id_match = re.search(r'P\d+', product_url)
                if id_match:
                    img_url = f"https://www.techlandbd.com/cache/images/uploads/products/{id_match.group()}/cover_cache_optimize-70.webp"
            
            # Absolute URL construction
            if img_url:
                if img_url.startswith('//'):
                    img_url = "https:" + img_url
                elif img_url.startswith('/') and not img_url.startswith('http'):
                    domain = re.match(r'(https?://[^/]+)', search_base).group(1)
                    img_url = domain + img_url
        except:
            pass 

        driver.quit()
        return {"price": price, "url": product_url, "image": img_url}
        
    except Exception:
        driver.quit()
        return {"price": None, "url": None, "image": None}

def check_health(store_name, store_config):
    """
    NEW: Performs a diagnostic test on a specific store.
    Uses a common term like 'RAM' to check if selectors are still valid.
    """
    # 
    try:
        # We use a very common item likely to be in stock for a reliable test
        test_result = search_and_get_price("RAM", store_name, store_config)
        
        if test_result["price"] is not None:
            return "✅ Online"
        elif test_result["url"] and test_result["url"].startswith("http"):
            # Price might be missing (out of stock) but URL works
            return "⚠️ Partial (Check Selectors)"
        else:
            return "❌ Selector Broken"
    except Exception as e:
        return f"🚨 Connection Failed"