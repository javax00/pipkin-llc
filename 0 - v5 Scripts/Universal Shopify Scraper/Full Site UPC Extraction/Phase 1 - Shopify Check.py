# pip install requests
import requests
import csv
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

def clean_store_url(raw_url: str) -> str:
    """Ensure URL has a scheme and no trailing slash."""
    if not raw_url.startswith(('http://', 'https://')):
        raw_url = 'https://' + raw_url
    parts = urlparse(raw_url)
    return f"{parts.scheme}://{parts.netloc}"

def fetch_page_products_with_retry(apikey: str, products_url: str, page: int, batch_end: int):
    """
    Fetch one page of products via ZenRows with up to 2 attempts.
    Prints when it starts processing.
    """
    print(f"Processing Url {page} of {batch_end}")
    zenrows_api = 'https://api.zenrows.com/v1/'
    params = {
        'url': f"{products_url}?limit=250&page={page}",
        'apikey': apikey,
        # 'premium_proxy': 'true',    # uncomment if needed
        # 'proxy_country': 'us',
    }

    for attempt in (1, 2):
        try:
            resp = requests.get(zenrows_api, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json().get('products', [])
        except requests.RequestException as e:
            print(f"  Error on page {page} (attempt {attempt}/2): {e}")
    print(f"  Skipping page {page} after 2 failed attempts.")
    return []

def main():
    apikey = ''
    sites_file = "P1 Shopify Sites.csv"
    output_file = "P1 Product Links.csv"

    # Read all store URLs
    with open(sites_file, newline='', encoding='utf-8') as sf:
        reader = csv.reader(sf)
        sites = [row[0].strip() for row in reader if row]

    # Prepare output (overwrite if existing)
    if os.path.exists(output_file):
        os.remove(output_file)

    with open(output_file, mode='w', newline='', encoding='utf-8') as outf:
        writer = csv.writer(outf)
        writer.writerow(['product_link'])

        for site in sites:
            store = clean_store_url(site)
            products_url = f"{store}/products.json"

            print(f"\nStarting Website – {store}")
            site_total = 0
            batch_start = 1

            # Process in batches of 5 pages
            while True:
                batch_end = batch_start + 5 - 1
                pages = list(range(batch_start, batch_end + 1))

                # Launch concurrent fetches for this batch
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(fetch_page_products_with_retry, apikey, products_url, page, batch_end): page
                        for page in pages
                    }

                    results = []
                    for fut in as_completed(futures):
                        page = futures[fut]
                        products = fut.result()
                        results.append((page, products))

                # Sort results by page number
                results.sort(key=lambda x: x[0])

                # If any page is empty, write what we have and stop this site
                if any(not prods for (_, prods) in results):
                    for page, prods in results:
                        if prods:
                            for p in prods:
                                handle = p.get('handle')
                                if handle:
                                    writer.writerow([f"{store}/products/{handle}"])
                                    site_total += 1
                            print(f"Processing Page {page} – {len(prods)} links extracted (total for this site: {site_total})")
                        else:
                            print(f"No products on page {page} → ending crawl for this site.")
                            break
                    break

                # Otherwise, all pages returned products; write them and continue
                for page, prods in results:
                    for p in prods:
                        handle = p.get('handle')
                        if handle:
                            writer.writerow([f"{store}/products/{handle}"])
                            site_total += 1
                    print(f"Processing Page {page} – {len(prods)} links extracted (total for this site: {site_total})")

                # Next batch
                batch_start += 5

            print(f"Finished {store}: extracted {site_total} links.")

    print(f"\nDone! All sites processed. See {output_file} for results.")

if __name__ == "__main__":
    main()

