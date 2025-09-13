import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import re
import math
import time
from bs4 import BeautifulSoup
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Load ZenRows API Key from .env ===
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")

def zenrows_request(target_url):
    zenrows_url = "https://api.zenrows.com/v1/"
    params = {
        'apikey': ZENROWS_API_KEY,
        'url': target_url,
        'js_render': 'true',
        'premium_proxy': 'true',
        'proxy_country': 'us',
        'custom_headers': 'true',
    }
    headers = {
        'nike-api-caller-id': 'nike:dotcom:browse:wall.client:2.0',
    }
    response = requests.get(zenrows_url, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    return response.text

url = "https://www.nike.com/w/back-to-school-sale-2083c"

# Get total products/pages
total_products = 0
while True:
    html = zenrows_request(url)
    soup = BeautifulSoup(html, "html.parser")
    count_span = soup.find("span", class_="wall-header__item_count")
    if count_span:
        numbers = re.findall(r"\d+", count_span.text)
        total_products = int(numbers[0]) if numbers else 0
    else:
        total_products = 0

    pages = math.ceil(total_products / 24)
    print("Total products:", total_products)
    print("Total pages (24 per page):", pages)
    
    if pages > 0:
        break
    else:
        print("No products found. Retrying now...")

# Thread worker to get all product URLs on a page
def get_product_urls(page):
    api_url = f"https://api.nike.com/discover/product_wall/v1/marketplace/US/language/en/consumerChannelId/d9a5bc42-4b9c-4976-858a-f159cf99c647?path=/w/back-to-school-sale-2083c&attributeIds=2df25f39-cc81-4565-8c09-24966627d48f&queryType=PRODUCTS&anchor={page}&count=24"
    try:
        result = zenrows_request(api_url)
        data = json.loads(result)
        product_urls = []
        for product in data.get('productGroupings', []):
            # Defensive: pdpUrl may not exist for some
            if product['products'] and 'pdpUrl' in product['products'][0] and 'url' in product['products'][0]['pdpUrl']:
                product_urls.append(product['products'][0]['pdpUrl']['url'])
        return product_urls
    except Exception as e:
        print(f"Error processing page {page}: {e}")
        return []

# Delete old CSV if exists
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "product_url.csv")
if os.path.exists(csv_path):
    os.remove(csv_path)

all_urls = set()
anchors = list(range(0, total_products+1, 24))

with ThreadPoolExecutor(max_workers=20) as executor:
    future_to_page = {executor.submit(get_product_urls, page): page for page in anchors}
    for future in as_completed(future_to_page):
        urls = future.result()
        for url in urls:
            all_urls.add(url)
        print(f"Processed anchor {future_to_page[future]}")

# Save to CSV
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['url'])
    for url in sorted(all_urls):
        writer.writerow([url])

print(f"Saved {len(all_urls)} product URLs to {csv_path}")
