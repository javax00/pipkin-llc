# pip install requests
import requests
import csv
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))

# Your ZenRows API key
apikey = 'ef95565cee4ff7e6df2a9caa8f503da7b988ac2e'

# Input & output filenames
input_csv = 'P1 Pagination Urls.csv'
output_csv = 'final_shopwss_' + date_now + '.csv'

# Mapping for fixed‐promo tags: numerator, denominator
promo_map = {
    'promo-2-for-16':      (16,  2),
    'promo-2-for-20':      (20,  2),
    'promo-2-for-30':      (30,  3),
    'promo-2-for-40':      (40,  2),
    'promo-2-for-50-nike': (50,  2),
    'promo-3-for-20':      (20,  3),
    'promo-3-for-32':      (32,  3),
}
# promo-socks-bogo is a 25% discount on the default cost

# Load all pagination URLs
with open(input_csv, newline='', encoding='utf-8') as f_in:
    reader = csv.reader(f_in)
    urls = [row[0] for row in reader]

total = len(urls)

def process_page(idx, page_url):
    print(f"Processing Url {idx} of {total}")

    # retry logic: up to 3 attempts
    for attempt in range(1, 4):
        try:
            # resp = requests.get(
            #     'https://api.zenrows.com/v1/',
            #     params={'url': page_url, 'apikey': apikey},
            #     timeout=60
            # )
            resp = requests.get(page_url, timeout=90)
            resp.raise_for_status()
            data = resp.json()
            break
        except (requests.exceptions.RequestException, ValueError):
            if attempt == 3:
                print(f"  ⚠️ Skipping after 3 failed attempts: {page_url}")
                return []  # skip this URL
            else:
                print(f"  Retry {attempt} failed, trying again...")

    rows = []
    for item in data.get('items', []):
        raw_tags = item.get('tags', '')
        tags_list = [
            t.strip() for t in raw_tags
                .replace('[:ATTR:]', ', ')
                .split(', ')
            if t.strip()
        ]

        for variant in item.get('shopify_variants', []):
            barcode = variant.get('barcode', '') or ''
            if not barcode:
                continue

            # default cost = min(price, list_price)
            price = float(variant.get('price', '0') or 0)
            list_price = float(variant.get('list_price', '0') or 0)
            cost_val = min(price, list_price) if list_price > 0 else price

            # check for a promo tag
            promo_tag = next((tag for tag in promo_map if tag in tags_list), None)

            # apply promo pricing
            if promo_tag:
                if promo_tag == 'promo-socks-bogo':
                    cost_val *= 0.75
                else:
                    num, den = promo_map[promo_tag]
                    raw_promo = num / den
                    cost_val = math.floor(raw_promo * 100) / 100

            # apply eligible-discount if present
            eligible = any(t.startswith('eligible-discount') for t in tags_list)
            if eligible:
                cost_val = math.floor(cost_val * 0.8 * 100) / 100

            # calculate ADJ
            adj_val = cost_val * (0.8 if eligible else 1)
            adj_str = f"{adj_val:.2f}"

            # decide which single tag to output
            if promo_tag:
                tag_output = promo_tag
            elif eligible:
                tag_output = 'eligible-discount'
            else:
                tag_output = ''

            # build full link
            rel_link = variant.get('link', '')
            abs_link = f"https://www.shopwss.com{rel_link}"

            barcode_prefixed = barcode
            rows.append([
                barcode_prefixed,
                adj_str,
                abs_link,
                tag_output
            ])

    return rows

# Write the CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(['Barcode', 'Cost', 'Source', 'Tag'])

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {
            executor.submit(process_page, idx, url): idx
            for idx, url in enumerate(urls, start=1)
        }
        for future in as_completed(futures):
            for row in future.result():
                writer.writerow(row)

print(f"Wrote {output_csv} ✔")
