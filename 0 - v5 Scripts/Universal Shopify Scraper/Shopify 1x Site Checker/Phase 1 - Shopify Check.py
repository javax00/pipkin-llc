# pip install requests
import requests
import urllib.parse
import csv
import threading
from concurrent.futures import ThreadPoolExecutor

ZENROWS_ENDPOINT = 'https://api.zenrows.com/v1/'
API_KEY = ''
INPUT_CSV = 'P1 Check Links.csv'
OUTPUT_CSV = 'P1 Shopify Check.csv'

def get_base_url(raw_url):
    """Normalize input to scheme://domain."""
    if '://' not in raw_url:
        raw_url = 'https://' + raw_url
    parsed = urllib.parse.urlparse(raw_url)
    return f"{parsed.scheme}://{parsed.netloc}"

def fetch_with_retry(target_url, use_premium=False):
    """Try ZenRows up to two times; return JSON or None."""
    params = {'url': target_url, 'apikey': API_KEY}
    if use_premium:
        params.update({'premium_proxy': 'true', 'proxy_country': 'us'})
    for attempt in range(2):
        try:
            resp = requests.get(ZENROWS_ENDPOINT, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError):
            continue
    return None

def main():
    # 1) Read all raw URLs from input CSV
    with open(INPUT_CSV, newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        urls = [row[0].strip() for row in reader if row]

    total = len(urls)

    # 2) Open output CSV once, write header
    lock = threading.Lock()
    csvfile = open(OUTPUT_CSV, 'w', newline='', encoding='utf-8')
    writer = csv.writer(csvfile)
    writer.writerow(['Urls', 'Proxy', 'Result'])

    def worker(idx, raw):
        # Print when this thread actually starts
        print(f"Processing Url {idx} of {total}")
        base = get_base_url(raw)
        products_url = f"{base}/products.json"

        # Attempt #1: No proxy
        data = fetch_with_retry(products_url, use_premium=False)
        if data and 'products' in data:
            with lock:
                for p in data['products']:
                    handle = p.get('handle')
                    if handle:
                        writer.writerow([f"{base}/products/{handle}", 'No proxy', 'Shopify'])
            return

        # Attempt #2: Premium proxy
        data = fetch_with_retry(products_url, use_premium=True)
        if data and 'products' in data:
            with lock:
                for p in data['products']:
                    handle = p.get('handle')
                    if handle:
                        writer.writerow([f"{base}/products/{handle}", 'Premium proxy', 'Shopify'])
        else:
            # Not Shopify
            with lock:
                writer.writerow([products_url, 'Premium proxy', 'Not Shopify'])

    # 3) Kick off ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as exec:
        for i, raw in enumerate(urls, start=1):
            exec.submit(worker, i, raw)

    # 4) Clean up
    csvfile.close()
    print(f"\nResults written to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
