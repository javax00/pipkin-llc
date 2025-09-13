# pip install requests
import requests
import csv
import re
import concurrent.futures

# === Configuration ===
INPUT_CSV    = 'P3 Pagination Urls Post Blacklist.csv'
ZENROWS_API  = 'https://api.zenrows.com/v1/'
API_KEY      = 'ef95565cee4ff7e6df2a9caa8f503da7b988ac2e'
TIMEOUT_SEC  = 60
MAX_ATTEMPTS = 2
MAX_WORKERS  = 50

# static headers (Referer injected per iteration)
BASE_HEADERS = {
    'Accept':           'application/json, text/javascript, */*; q=0.01',
    'Origin':           'https://www.kohls.com',
    'X-Requested-With': 'XMLHttpRequest',
}

FIELDNAMES = ['SkuCode', 'Price', 'Quantity', 'UPC', 'Promo', 'Source']

# === 1) Load all URLs from CSV ===
with open(INPUT_CSV, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    urls = [row[0].strip() for row in reader if row]

total = len(urls)

def fetch_for_url(idx, full_url):
    # Print inside worker when it starts
    print(f"Processing Url {idx} of {total}")
    rows = []
    m = re.search(r'/prd-(\d+)', full_url)
    if not m:
        return rows  # skip if no PRD

    prd = m.group(1)
    kohl_api_url = f'https://www.kohls.com/web/productInventoryPrice/{prd}?storeNum='
    params = {
        'apikey':         API_KEY,
        'url':            kohl_api_url,
        'custom_headers': 'true',
    }

    headers = BASE_HEADERS.copy()
    headers['Referer'] = full_url

    # retry logic
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.post(
                ZENROWS_API,
                params=params,
                headers=headers,
                json={},
                timeout=TIMEOUT_SEC
            )
            if resp.status_code == 200:
                data = resp.json()
                break
        except requests.RequestException:
            pass
    else:
        return rows  # skip on repeated failure

    products = data.get('payload', {}).get('products', [])
    for product in products:
        skus   = product.get('SKUS', [])
        prices = product.get('prices', [])

        for sku in skus:
            sku_code  = sku.get('skuCode', '')
            price_idx = sku.get('priceIndex')
            qty       = sku.get('onlineAvailableQty', '')
            upc_id    = sku.get('UPC', {}).get('ID', '')

            matched = next((p for p in prices if p.get('index') == price_idx), {})
            suppressed = matched.get('suppressedPricingText')
            price = suppressed if suppressed else matched.get('lowestApplicablePrice', '')

            promo = (matched.get('promotion') or {}).get('bogo') or ''

            source = f"{full_url}?skuid={sku_code}"
            upc    = f"{upc_id}"

            rows.append({
                'SkuCode':  sku_code,
                'Price':    price,
                'Quantity': qty,
                'UPC':      upc,
                'Promo':    promo,
                'Source':   source,
            })

    return rows

# === 2) Parallel execution ===
all_rows = []
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [
        executor.submit(fetch_for_url, idx, url)
        for idx, url in enumerate(urls, start=1)
    ]
    for future in concurrent.futures.as_completed(futures):
        all_rows.extend(future.result())

# === 3) Split and write outputs ===
needs_price = [r for r in all_rows if r['Price'] == 'FOR PRICE, ADD TO BAG']
upcs_only   = [r for r in all_rows if r['Price'] != 'FOR PRICE, ADD TO BAG']

with open('P3 Add to Cart Needs Price Check.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(needs_price)
print(f"Wrote {len(needs_price)} rows to P3 Add to Cart Needs Price Check.csv")

with open('P3 UPCs.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(upcs_only)
print(f"Wrote {len(upcs_only)} rows to P3 UPCs.csv")

