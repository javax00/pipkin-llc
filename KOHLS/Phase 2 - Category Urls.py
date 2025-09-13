# pip install requests bs4
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
from concurrent.futures import ThreadPoolExecutor

ZENROWS_API = 'https://api.zenrows.com/v1/'
API_KEY = 'ef95565cee4ff7e6df2a9caa8f503da7b988ac2e'
BASE_URL = 'https://www.kohls.com'
INPUT_FILENAME = 'P1 Pagination.csv'
OUTPUT_FILENAME = 'P2 Pagination Urls.csv'
MAX_RETRIES = 3
TIMEOUT = 60

def process_page(idx, page_url, total):
    print(f"Processing Url {idx} of {total}")
    page_links = []
    for attempt in range(1, MAX_RETRIES + 1):
        params = {
            'url':       page_url,
            'apikey':    API_KEY,
            'js_render': 'true',
            'wait_for':  'div.prod_img_block',
        }
        if attempt > 1:
            params.update({
                'premium_proxy': 'true',
                'proxy_country': 'us',
            })
        try:
            resp = requests.get(ZENROWS_API, params=params, timeout=TIMEOUT)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')
            anchors = soup.select('div.prod_img_block a')
            if not anchors:
                raise ValueError("No links found on page")

            for a in anchors:
                href = a.get('href')
                if not href:
                    continue
                clean = href.split('?', 1)[0]
                absolute = urljoin(BASE_URL, clean)
                page_links.append(absolute)

            break  # success, exit retry loop

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  Attempt {attempt} failed: {e}. Retrying...")
            else:
                print(f"  Attempt {attempt} failed: {e}. Skipping this URL.")

    return page_links

# load input URLs
with open(INPUT_FILENAME, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    input_urls = [row[0] for row in reader if row]

total_pages = len(input_urls)
all_links = []

# process pages in parallel
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = [
        executor.submit(process_page, idx, url, total_pages)
        for idx, url in enumerate(input_urls, start=1)
    ]
    for future in futures:
        all_links.extend(future.result())

# remove duplicates
total_found = len(all_links)
seen = set()
unique_links = []
for link in all_links:
    if link not in seen:
        seen.add(link)
        unique_links.append(link)

duplicates = total_found - len(unique_links)
if duplicates:
    print(f"Detected and deleted {duplicates} duplicate URLs")

# write to CSV (no headers), overwrite if exists
with open(OUTPUT_FILENAME, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    for link in unique_links:
        writer.writerow([link])

print(f"Wrote {len(unique_links)} URLs to {OUTPUT_FILENAME}")
