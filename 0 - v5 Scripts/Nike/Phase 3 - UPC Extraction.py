# pip install requests
import csv
import requests
from concurrent.futures import ThreadPoolExecutor

# ZenRows parameters
ZENROWS_ENDPOINT = 'https://api.zenrows.com/v1/'
API_KEY = ''
BASE_URL = (
    'https://api.nike.com/discover/product_details_availability/'
    'v1/marketplace/US/language/en/consumerChannelId/'
    'd9a5bc42-4b9c-4976-858a-f159cf99c647/groupKey/'
)

# Input & output files
input_file = 'P2 Pagination Urls.csv'
output_file = 'P3 UPCs.csv'

# 1. Load unique groupKeys from P2 Pagination Urls
group_keys = []
with open(input_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = row['groupKey']
        if key not in group_keys:
            group_keys.append(key)

total = len(group_keys)

def fetch_and_extract(idx_key):
    idx, key = idx_key
    print(f"Processing Url {idx} of {total}")
    target_url = BASE_URL + key

    # retry logic
    data = None
    for attempt in (1, 2):
        try:
            resp = requests.get(
                ZENROWS_ENDPOINT,
                params={'url': target_url, 'apikey': API_KEY, 'custom_headers': 'true'},
                headers={'nike-api-caller-id': 'com.nike.commerce.nikedotcom.web'},
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.RequestException as e:
            print(f"  Attempt {attempt} failed for groupKey {key}: {e}")
            if attempt == 2:
                print(f"  Skipping groupKey {key} after 2 failed attempts\n")

    if not data:
        return []  # no rows for this key

    rows = []
    for size in data.get('sizes', []):
        avail = size.get('availability', {})
        if not avail.get('isAvailable', False):
            continue
        raw_gtin = size.get('gtin', '')
        trimmed = raw_gtin[2:] if raw_gtin.startswith('00') else raw_gtin
        quoted_gtin = f"'{trimmed}"
        product_code = size.get('productCode', '')
        ship = avail.get('ship', '')
        rows.append([key, quoted_gtin, product_code, 'true', ship])

    return rows

# 2. Run with concurrency and write output
with open(output_file, 'w', newline='', encoding='utf-8') as out_f:
    writer = csv.writer(out_f)
    writer.writerow(['groupKey', 'GTIN', 'productCode', 'isAvailable', 'ship'])

    with ThreadPoolExecutor(max_workers=40) as executor:
        for result_rows in executor.map(fetch_and_extract, enumerate(group_keys, start=1)):
            for row in result_rows:
                writer.writerow(row)

print(f"\nDone! Wrote in-stock UPCs for {total} groupKeys to {output_file}")
