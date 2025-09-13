# pip install requests beautifulsoup4
import requests
import re
import csv
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading

# --- configuration ---
input_csv   = 'P2 Category Urls.csv'
output_csv  = 'P3 MGAE Quantity Source.csv'
apikey      = ''
zenrows_api = 'https://api.zenrows.com/v1/'

# --- load URLs ---
with open(input_csv, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    urls = [row[0] for row in reader if row]

total = len(urls)

# --- prepare CSV writing and thread lock ---
lock = threading.Lock()
csvfile = open(output_csv, mode='w', newline='', encoding='utf-8')
writer = csv.writer(csvfile)
writer.writerow(['Price', 'UPC', 'Quantity', 'Source'])

def process_url(index, url, total):
    print(f"Processing Url {index} of {total}")

    # fetch with one retry on failure
    html = None
    for attempt in (1, 2):
        try:
            resp = requests.get(
                zenrows_api,
                params={'url': url, 'apikey': apikey},
                timeout=60
            )
            resp.raise_for_status()
            html = resp.text
            break
        except requests.RequestException as e:
            if attempt == 1:
                print(f"  ⚠️ Attempt 1 failed ({e}), retrying...")
            else:
                print(f"  ❌ Attempt 2 failed for Url {index}, skipping.")
    if html is None:
        return

    # extract UPC
    upc_match = re.search(r'"gtin":"(\d+)"', html)
    upc       = upc_match.group(1) if upc_match else ''
    upc       = f"'{upc}"

    # parse for price & quantity
    soup      = BeautifulSoup(html, 'html.parser')
    price_tag = soup.find('span', class_='price price_regular')
    price     = price_tag.get_text(strip=True) if price_tag else ''

    qty_tag = soup.find('span', class_='product-page__low-quantity-notification')
    if qty_tag:
        m = re.search(r'Only\s+(\d+)\s+left', qty_tag.get_text())
        quantity = m.group(1) if m else ''
    else:
        quantity = ''

    # write row safely
    with lock:
        writer.writerow([price, upc, quantity, url])

# --- run with concurrency ---
with ThreadPoolExecutor(max_workers=5) as executor:
    for i, url in enumerate(urls, start=1):
        executor.submit(process_url, i, url, total)

csvfile.close()
print(f"Data written to {output_csv}")