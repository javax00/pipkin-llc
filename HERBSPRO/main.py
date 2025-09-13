import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import math
import concurrent.futures
import csv

# Load ZenRows API key
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")

zenrows_url = "https://api.zenrows.com/v1/"
base_url = "https://www.herbspro.com/collections/bogo-ca"

params_base = {
    'apikey': ZENROWS_API_KEY,
    'premium_proxy': 'true',
    'js_render': 'true',
    'proxy_country': 'us'
}

# Step 1: Get total products
params = params_base.copy()
params['url'] = base_url
r = requests.get(zenrows_url, params=params, timeout=60)
soup = BeautifulSoup(r.text, "html.parser")

total_products = int(soup.find("p", id="CollectionProductCount").text.strip().split(' ')[0])
print(f"Total products: {total_products}")

products_per_page = 24
total_pages = math.ceil(total_products / products_per_page)
print(f"Total pages to scrape: {total_pages}")

# Step 2: Scrape each paginated page for product links
all_product_links = []

for i in range(1, total_pages + 1):
    page_url = f"{base_url}?page={i}"
    print(f"Scraping page {i}/{total_pages}: {page_url}")
    params = params_base.copy()
    params['url'] = page_url
    try:
        r = requests.get(zenrows_url, params=params, timeout=60)
        soup = BeautifulSoup(r.text, "html.parser")
        collection_grid = soup.find("div", id="main-collection-product-grid")
        if not collection_grid:
            print("No main-collection-product-grid found on this page.")
            continue
        cards = collection_grid.find_all("div", class_="cust-pdp-card")
        for card in cards:
            first_a = card.find("a", href=True)
            if first_a:
                product_href = first_a['href']
                # Normalize relative URLs
                if product_href.startswith("/"):
                    product_href = "https://www.herbspro.com" + product_href
                all_product_links.append(product_href)
    except Exception as e:
        print(f"Error scraping page {i}: {e}")

print(f"\nTotal product links collected: {len(all_product_links)}")

# Step 3: Prepare CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'final_herbspro.csv')
if os.path.exists(csv_file):
    os.remove(csv_file)
    print(f"Deleted existing file: {csv_file}")

header = ['UPC', 'PRICE', 'SOURCE LINK']
with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)

# Step 4: Threaded scraping of product .json endpoints
def fetch_upc_price(link):
    upc, price = '', ''
    params_json = {
        'apikey': ZENROWS_API_KEY,
        'url': link + '.json'
    }
    try:
        r = requests.get(zenrows_url, params=params_json, timeout=40)
        json_data = r.json()
        upc = json_data['product']['variants'][0].get('barcode', '')
        price = json_data['product']['variants'][0].get('price', '')
    except Exception as e:
        print(f"Error scraping product {link}: {e}")
    return ['\''+upc, price, link]

results = []

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Show a basic progress indicator
    future_to_link = {executor.submit(fetch_upc_price, link): link for link in all_product_links}
    for i, future in enumerate(concurrent.futures.as_completed(future_to_link), 1):
        data = future.result()
        results.append(data)
        print(f"{i}/{len(all_product_links)}")

# Step 5: Write results to CSV
with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(results)

print(f"\nDone! Saved {len(results)} rows to {csv_file}")
