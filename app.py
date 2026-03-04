import streamlit as st
import time
import concurrent.futures
import pandas as pd
from scraper import search_and_get_price, check_health
from database import init_db, add_shop, get_shops, delete_shop, update_shop, log_search, get_search_stats

# --- INITIALIZATION ---
st.set_page_config(page_title="Price Hunter Pro", layout="wide", page_icon="🛍️")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- CUSTOM UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 50px; background-color: #ff4b4b; color: white; font-weight: bold; width: 100%; }
    [data-testid="column"] { 
        min-height: 520px; background: white; padding: 20px; border-radius: 15px; border: 1px solid #eee; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .winner-badge { background-color: #28a745; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; display: inline-block; margin-bottom: 10px; }
    .quotation-box { background-color: #f1f3f6; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio("Go to:", ["Search Products", "PC Builder", "Admin Dashboard"])

def login():
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔒 Admin Access")
    user = st.sidebar.text_input("Username", key="sidebar_user")
    pw = st.sidebar.text_input("Password", type="password", key="sidebar_pw")
    if st.sidebar.button("Login", key="sidebar_login_btn"):
        if user == "admin" and pw == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials")

# --- PAGE 1: SEARCH PRODUCTS ---
if page == "Search Products":
    st.title("🏹 Ultimate Tech Price Hunter")
    st.write("Compare all stores at once with multi-threaded speed.")
    
    query = st.text_input("What are you hunting for?", placeholder="e.g. Archer C80", key="main_search_input")
    current_shops = get_shops()
    
    if st.button("Start Global Search", key="search_trigger"):
        if not current_shops:
            st.warning("⚠️ No shops found. Add them in the Admin Dashboard.")
        elif query:
            log_search(query)
            shop_names = list(current_shops.keys())
            cols = st.columns(len(shop_names))
            placeholders = [col.empty() for col in cols]
            
            with st.status("🚀 Launching parallel hunting bots...", expanded=True) as status:
                all_results = {}
                shared_image = None
                valid_prices = []

                def fetch_task(name, config):
                    try: return name, search_and_get_price(query, name, config)
                    except: return name, {"price": None, "image": None, "url": None}

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = {executor.submit(fetch_task, n, c): n for n, c in current_shops.items()}
                    for future in concurrent.futures.as_completed(futures):
                        s_name, s_data = future.result()
                        all_results[s_name] = s_data
                        if s_data.get("image") and not shared_image: shared_image = s_data["image"]
                        if s_data.get("price"): valid_prices.append(s_data["price"])

                min_price = min(valid_prices) if valid_prices else None

                for i, name in enumerate(shop_names):
                    res = all_results.get(name, {"price": None, "image": None, "url": None})
                    img = res.get("image") if res.get("image") else shared_image
                    price = res.get("price")
                    is_best = (price == min_price and min_price is not None)
                    
                    with placeholders[i].container():
                        if is_best: st.markdown('<div class="winner-badge">✨ BEST VALUE</div>', unsafe_allow_html=True)
                        st.subheader(name.capitalize())
                        if img: st.image(img, use_container_width=True)
                        if price:
                            st.metric("Price", f"{int(price)} Tk", delta="- Lowest" if is_best else None)
                            prod_url = res.get("url")
                            if prod_url and prod_url.startswith("http"):
                                # FIXED: Removed 'key' to avoid TypeError
                                st.link_button("View Product", prod_url)
                        else: st.error("Out of Stock")
                status.update(label="✅ Search Complete!", state="complete")

# --- PAGE 2: PC BUILDER (PRO COMPATIBILITY MODE) ---
elif page == "PC Builder":
    st.title("🖥️ Smart Component Selection (Compatibility Mode)")
    st.write("Pick a Processor, and we'll filter motherboards based on specific Intel/AMD sockets.")

    # 1. COMPATIBILITY MAPPING (Based on provided documentation)
    cpu_options = {
        "Intel Core Ultra 200 (15th Gen)": ("LGA1851", "Intel"),
        "Intel Core 14th/13th/12th Gen": ("LGA1700", "Intel"),
        "Intel Core 11th/10th Gen": ("LGA1200", "Intel"),
        "Intel Core 9th/8th Gen": ("LGA1151", "Intel"),
        "Ryzen 9000/8000/7000 Series": ("AM5", "AMD"),
        "Ryzen 5000/3000 Series": ("AM4", "AMD")
    }

    mb_options = {
        "LGA1851": ["Z890 Motherboard", "B860 Motherboard"],
        "LGA1700": ["Z790 Motherboard", "B760 Motherboard", "H610 Motherboard"],
        "LGA1200": ["Z590 Motherboard", "B560 Motherboard", "H510 Motherboard"],
        "LGA1151": ["Z390 Motherboard", "B365 Motherboard", "H310 Motherboard"],
        "AM5": ["X870 Motherboard", "X670 Motherboard", "B650 Motherboard"],
        "AM4": ["X570 Motherboard", "B550 Motherboard", "A520 Motherboard", "B450 Motherboard"]
    }

    # 2. SELECTION UI
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Core Components")
        selected_cpu_fam = st.selectbox("Select CPU Family", list(cpu_options.keys()))
        socket = cpu_options[selected_cpu_fam][0]
        st.info(f"Required Socket: **{socket}**")
        
        compatible_mbs = mb_options.get(socket, ["Universal Motherboard"])
        selected_mb = st.selectbox("Select Compatible Motherboard", compatible_mbs)
        
        specific_cpu = st.text_input("Enter Specific CPU Model (Optional)", placeholder="e.g. Core i5-13400")
        final_cpu_query = specific_cpu if specific_cpu else selected_cpu_fam

    with c2:
        st.subheader("Supporting Parts")
        ram_type = "DDR5" if socket in ["AM5", "LGA1851"] else "DDR4"
        selected_ram = st.selectbox(f"Memory ({ram_type})", [f"Corsair 16GB {ram_type}", f"G.Skill 8GB {ram_type}"])
        selected_ssd = st.selectbox("Storage", ["Samsung 500GB NVMe", "HP 250GB SSD", "Western Digital 1TB"])
        selected_psu = st.selectbox("Power Supply", ["Antec 450W", "Corsair 550W", "Cooler Master 650W"])

    # 3. GENERATION LOGIC
    if st.button("Generate Compatible Quotation", key="gen_pro_build"):
        current_shops = get_shops()
        if not current_shops:
            st.error("Please add shops in Admin Dashboard first.")
        else:
            build_items = {"CPU": final_cpu_query, "Motherboard": selected_mb, "RAM": selected_ram, "SSD": selected_ssd, "PSU": selected_psu}
            build_results = []
            total_cost = 0
            
            
            
            with st.status("🛠️ Multi-threading price comparison...", expanded=True) as status:
                for part_type, query in build_items.items():
                    status.write(f"Searching for best **{query}** deal...")
                    prices = []
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {executor.submit(search_and_get_price, query, n, c): n for n, c in current_shops.items()}
                        for f in concurrent.futures.as_completed(futures):
                            res = f.result()
                            if res.get("price"):
                                prices.append((res['price'], futures[f], res['url']))
                    
                    if prices:
                        prices.sort(key=lambda x: x[0])
                        p, s, l = prices[0]
                        build_results.append({"Category": part_type, "Model": query, "Shop": s.capitalize(), "Price": int(p), "URL": l})
                        total_cost += p
                    else:
                        build_results.append({"Category": part_type, "Model": query, "Shop": "N/A", "Price": 0, "URL": ""})

                status.update(label="✅ Quotation Complete!", state="complete")

            # Final Table
            df_build = pd.DataFrame(build_results)
            st.table(df_build[["Category", "Model", "Shop", "Price"]])
            st.markdown(f"### 💰 Total Build Cost: **{int(total_cost)} Tk**")
            
            csv = df_build.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Quotation (CSV)", data=csv, file_name="pro_pc_build.csv", mime="text/csv")

# --- PAGE 3: ADMIN DASHBOARD ---
elif page == "Admin Dashboard":
    if not st.session_state.logged_in:
        st.title("🛡️ Restricted Access")
        login()
    else:
        st.title("⚙️ Admin Control Panel")
        if st.sidebar.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

        t1, t2, t3 = st.tabs(["📊 Analytics", "🛠️ Inventory", "🏥 Health Check"])

        with t1:
            stats = get_search_stats()
            if not stats.empty:
                st.bar_chart(stats.set_index('query'))
                st.table(stats)
            else: st.info("No data logged yet.")

        with t2:
            with st.expander("➕ Add New Shop"):
                with st.form(key="add_shop_form_final"):
                    n = st.text_input("Name")
                    u = st.text_input("Search URL")
                    t = st.text_input("CSS Tag")
                    if st.form_submit_button("Save"):
                        if n and u and t: add_shop(n, u, t); st.rerun()

            shops = get_shops()
            for name, conf in shops.items():
                c1, c2, c3, c4 = st.columns([2, 4, 1, 1])
                c1.write(f"**{name}**")
                c2.caption(f"Tag: {conf['price_tag']}")
                if c3.button("📝", key=f"ed_{name}"): st.session_state[f"mode_{name}"] = True
                if c4.button("🗑️", key=f"dl_{name}"): delete_shop(name); st.rerun()

                if st.session_state.get(f"mode_{name}", False):
                    with st.form(key=f"edit_f_{name}"):
                        en = st.text_input("Name", value=name)
                        eu = st.text_input("URL", value=conf['search_url'])
                        et = st.text_input("Tag", value=conf['price_tag'])
                        if st.form_submit_button("Update"):
                            update_shop(name, en, eu, et)
                            st.session_state[f"mode_{name}"] = False; st.rerun()
                st.divider()

        with t3:
            if st.button("Run Diagnostic", key="h_diag"):
                shops = get_shops()
                with st.status("Testing scrapers...") as s:
                    results = {}
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        futs = {ex.submit(check_health, n, c): n for n, c in shops.items()}
                        for f in concurrent.futures.as_completed(futs): results[futs[f]] = f.result()
                    s.update(label="Diagnostic Finished", state="complete")
                st.table([{"Store": k, "Status": v} for k, v in results.items()]) 
