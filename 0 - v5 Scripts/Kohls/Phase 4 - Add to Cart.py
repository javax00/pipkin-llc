# pip install requests
import requests
import csv
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# ZenRows endpoint and your API key
ZENROWS_API = 'https://api.zenrows.com/v1/'
API_KEY     = 'ef95565cee4ff7e6df2a9caa8f503da7b988ac2e'

# The Kohl’s add-to-cart endpoint
TARGET_URL = 'https://www.kohls.com/cnc/checkout/cartItems/addItemToCart'

# Base headers (we'll override 'referer' per-row)
BASE_HEADERS = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://www.kohls.com',
}

# Tell ZenRows to forward your headers
ZENROWS_PARAMS = {
    'url': TARGET_URL,
    'apikey': API_KEY,
    'custom_headers': 'true'
}

# Input and output files
INPUT_CSV  = "P3 Add to Cart Needs Price Check.csv"
OUTPUT_CSV = "P4 Add to Cart Checked.csv"
if not OUTPUT_CSV.lower().endswith('.csv'):
    OUTPUT_CSV += '.csv'

# Load all rows so we know the total count
with open(INPUT_CSV, newline='', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    rows   = list(reader)

total = len(rows)

def process_row(idx, row):
    # Print inside each worker when it starts
    print(f"Processing Url {idx} of {total}")

    source_url = row['Source']
    sku_code   = row['SkuCode']
    # Always send quantity = 1
    quantity   = 1

    # Extract productId from the source URL (e.g., /prd-5168844/)
    m = re.search(r'/prd-(\d+)', source_url)
    product_id = m.group(1) if m else ''

    # Build headers for this iteration
    headers = BASE_HEADERS.copy()
    headers['referer'] = source_url

    # Build payload
    payload = {
        "cartItems": [
            {
                "productId":    product_id,
                "quantity":     quantity,
                "registryInfo": None,
                "skuId":        sku_code,
                "incentiveStore": "1032"
            }
        ],
        "source": "snb",
        "promocode": []
    }

    # Retry logic: up to 2 attempts
    data = None
    for attempt in (1, 2):
        try:
            resp = requests.post(
                ZENROWS_API,
                params=ZENROWS_PARAMS,
                headers=headers,
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            break
        except (requests.exceptions.RequestException, ValueError) as e:
            if attempt < 2:
                print(f"  ⚠️ Attempt {attempt} failed for Url {idx}: {e}. Retrying…")
            else:
                print(f"  ❌ Attempt {attempt} failed for Url {idx}: {e}. Skipping.")
    if data is None:
        return None

    # Parse response
    try:
        item = data['cartItems'][0]
        upc  = item.get('upcCode', '')
        cost = item.get('itemPriceInfo', {}).get('saleUnitprice', '')
    except (KeyError, IndexError):
        print(f"  ⚠️ Unexpected JSON structure for Url {idx}, skipping:", data)
        return None

    # Format UPC and set blank Promo
    upc_formatted = f"'{upc}"
    promo = ''

    # Return a row matching the header: SkuCode, Price, Quantity, UPC, Promo, Source
    return [sku_code, cost, quantity, upc_formatted, promo, source_url]

# Run concurrent processing
results = []
with ThreadPoolExecutor(max_workers=50) as executor:
    future_to_idx = {
        executor.submit(process_row, idx, row): idx
        for idx, row in enumerate(rows, start=1)
    }
    for future in as_completed(future_to_idx):
        row_result = future.result()
        if row_result:
            results.append(row_result)

# Write out the CSV (overwrite if exists)
with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['SkuCode', 'Price', 'Quantity', 'UPC', 'Promo', 'Source'])
    writer.writerows(results)

print(f"\nDone — processed {total} rows, output saved to {os.path.abspath(OUTPUT_CSV)}")
