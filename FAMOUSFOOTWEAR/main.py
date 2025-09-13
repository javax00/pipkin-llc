import requests
import time
from dotenv import load_dotenv
from pathlib import Path
import os
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))
# Path setup and delete old CSV if present
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'product_url_' + date_now + '.csv')
if os.path.exists(csv_file):
    os.remove(csv_file)
    print(f"Deleted existing file: {csv_file}")

# Load API key from .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
zenrows_api_key = os.getenv('ZENROWS_API_KEY')
if not zenrows_api_key:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")

zenrows_url = "https://api.zenrows.com/v1/"

def fetch_urls_from_page(page, first_page_soup=None):
    if first_page_soup:
        soup = first_page_soup
    else:
        # target_url = f"https://www.famousfootwear.com/browse/promotion/athletics#page={page}"
        target_url = f"https://www.famousfootwear.com/browse/sale/adidas?icid=hp_offer_shpnw_30offadidas&?boosteditem=[30986,30931,30932,44666]#page={page}"
        params = {
            'url': target_url,
            'apikey': zenrows_api_key,
            'premium_proxy': 'true',
            'proxy_country': 'us',
            'js_render': 'true',
            'antibot': 'true',
            'wait_for': '._layout2TopLeftColumnTop_1wmod_63'
        }
        try:
            r = requests.get(zenrows_url, params=params, timeout=90)
            r.raise_for_status()  # Check for HTTP errors
            soup = BeautifulSoup(r.text, "html.parser")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            return [], False, None

    product_grids = soup.find_all("div", class_="CoveoHeadlessResult")
    urls = []
    for grid in product_grids:
        a_tag = grid.find("a", class_="_productImageLink_onc2y_195")
        if a_tag:
            # Extract the URL and remove the part after the last "/"
            url = "https://www.famousfootwear.com" + a_tag.get("href")
            cleaned_url = url.rsplit('/', 1)[0]  # Remove everything after the last "/"
            urls.append(cleaned_url)

    page_div = soup.find("div", class_="_layout2TopLeftColumnTop_1wmod_63")
    is_last_page = False
    total_pages = None
    if page_div:
        getPage = page_div.find_all("span")[0].text.split(" ")
        startProduct = int(getPage[0].replace(',', ''))
        endProduct = int(getPage[2].replace(',', ''))
        totalProducts = int(getPage[4].replace(',', ''))
        products_per_page = endProduct - startProduct + 1
        total_pages = (totalProducts + products_per_page - 1) // products_per_page
        is_last_page = endProduct >= totalProducts
    else:
        is_last_page = True

    return urls, is_last_page, total_pages

# First, fetch page 0 to get both initial URLs and total page count
first_page_urls, _, total_pages = fetch_urls_from_page(0, first_page_soup=None)
if total_pages is None or total_pages == 0:
    print("No products found or failed to determine total pages.")
    exit()

print(f"Total pages: {total_pages}")

# Prepare thread pool for remaining pages (1..total_pages-1)
all_urls = list(first_page_urls)
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = []
    for page in range(1, total_pages):
        futures.append(executor.submit(fetch_urls_from_page, page))

    for i, future in enumerate(as_completed(futures), start=1):
        try:
            urls, _, _ = future.result()
            all_urls.extend(urls)
            if i % 10 == 0 or i == total_pages - 1:
                print(f"Progress: {i+1}/{total_pages} pages scraped.")
        except Exception as e:
            print(f"Exception fetching a page: {e}")

# Deduplicate and sort URLs
all_urls = sorted(set(all_urls))

# Save cleaned, unique URLs to CSV in the same directory as main.py
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Product URL'])
    for url in all_urls:
        writer.writerow([url])

print("="*40)
print(f"Saved {len(all_urls)} product URLs to {csv_file}")
print("="*40)
