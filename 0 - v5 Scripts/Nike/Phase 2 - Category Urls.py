# pip install requests
import requests
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ZenRows endpoint and your API key
ZENROWS_API = 'https://api.zenrows.com/v1/'
API_KEY     = ''

# Input and output CSV filenames
INPUT_CSV  = 'P1 Pagination Urls.csv'
OUTPUT_CSV = 'P2 Pagination Urls.csv'

# Read all URLs from the input file (one per line, starting at cell A1)
with open(INPUT_CSV, newline='', encoding='utf-8') as infile:
    urls = [row[0].strip() for row in csv.reader(infile) if row and row[0].strip()]

total_urls = len(urls)

# Prepare CSV writer (thread-safe)
outfile = open(OUTPUT_CSV, 'w', newline='', encoding='utf-8')
fieldnames = ['groupKey', 'productCode', 'currentPrice', 'url', 'title', 'promotionId']
writer = csv.DictWriter(outfile, fieldnames=fieldnames)
writer.writeheader()

empty_count = 0
empty_lock  = threading.Lock()
stop_event  = threading.Event()
write_lock  = threading.Lock()

def process_url(idx, fetch_url):
    global empty_count

    # If we've hit too many empties, skip immediately
    if stop_event.is_set():
        return

    print(f"Processing Url {idx} of {total_urls}")

    # --- error handling with one retry ---
    data = None
    for attempt in (1, 2):
        try:
            resp = requests.get(
                ZENROWS_API,
                params={
                    'url':            fetch_url,
                    'apikey':         API_KEY,
                    'premium_proxy':  'true',
                    'custom_headers': 'true',
                },
                headers={'nike-api-caller-id': 'nike:dotcom:browse:wall.client:2.0'},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception:
            if attempt < 2:
                print(f"  ⚠️  Error on attempt {attempt} for URL {idx}, retrying...")
            else:
                print(f"  ❌  Failed to fetch URL {idx} after 2 attempts; skipping.")
    if data is None:
        return

    # --- check for empty result ---
    groupings = data.get('productGroupings', [])
    total_products = sum(len(g.get('products', [])) for g in groupings)
    if total_products == 0:
        with empty_lock:
            empty_count += 1
            print(f"  ⚠️  No products returned (empty count: {empty_count})")
            if empty_count > 5:
                print("  🚫  More than 5 consecutive empty results—stopping iteration.")
                stop_event.set()
        return
    else:
        with empty_lock:
            empty_count = 0

    # --- write rows for each product ---
    with write_lock:
        for grouping in groupings:
            for product in grouping.get('products', []):
                prices   = product.get('prices') or {}
                promo    = product.get('promotions') or {}
                vis_list = promo.get('visibilities') or []

                writer.writerow({
                    'groupKey':     product.get('groupKey', ''),
                    'productCode':  product.get('productCode', ''),
                    'currentPrice': prices.get('currentPrice', ''),
                    'url':          product.get('pdpUrl', {}).get('url', ''),
                    'title':        vis_list[0].get('title', '') if vis_list else '',
                    'promotionId':  promo.get('promotionId', ''),
                })

# --- run with 5 concurrent workers ---
with ThreadPoolExecutor(max_workers=40) as executor:
    futures = [
        executor.submit(process_url, idx, url)
        for idx, url in enumerate(urls, start=1)
    ]
    # wait for all tasks to complete (or be skipped)
    for _ in as_completed(futures):
        pass

outfile.close()
print(f"All done — wrote data for up to {total_urls} URLs into {OUTPUT_CSV}")