# pip install requests
import csv
import requests
import os
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# ── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_CSV         = "P1 Shopify Check.csv"
OUTPUT_CSV        = "P2 UPC Check.csv"
RESULTS_CSV       = "P2 UPC Check results.csv"
ZENROWS_URL       = "https://api.zenrows.com/v1/"
API_KEY           = ""
MAX_WORKERS       = 20
TIMEOUT           = 60  # seconds per request attempt

# ── LOAD & FILTER ────────────────────────────────────────────────────────────
with open(INPUT_CSV, newline="", encoding="utf-8") as f_in:
    reader       = csv.DictReader(f_in)
    all_rows     = list(reader)
    shopify_rows = [
        r for r in all_rows
        if r["Result"].strip().lower() == "shopify"
    ]

total_rows        = len(all_rows)
total_shopify     = len(shopify_rows)
non_shopify_count = total_rows - total_shopify

if total_shopify == 0:
    print(f"No Shopify rows found ({non_shopify_count} non-Shopify skipped).")
    exit()

# ── PREP OUTPUT ────────────────────────────────────────────────────────────────
for fn in (OUTPUT_CSV, RESULTS_CSV):
    if os.path.exists(fn):
        os.remove(fn)

lock = threading.Lock()

# overall invalid counters (for console summary)
blank_count       = 0
non_numeric_count = 0
length_count      = 0

# domain-level stats
# stats[domain] = {"checked": int, "valid": int}
domain_stats = defaultdict(lambda: {"checked": 0, "valid": 0})

# ── SET UP MAIN OUTPUT ─────────────────────────────────────────────────────────
f_out = open(OUTPUT_CSV, "w", newline="", encoding="utf-8")
writer = csv.writer(f_out)
writer.writerow([
    "Variant URL",
    "Price",
    "Barcode",
    "Available",
    "Proxy"
])

def process_row(idx, row):
    global blank_count, non_numeric_count, length_count

    raw_url = row["Urls"].strip().rstrip("/")
    parsed  = urlparse(raw_url)
    domain  = parsed.netloc.lower()

    with lock:
        print(f"Processing Url {idx} of {total_shopify} ({domain})")

    # decide proxy
    is_premium = row["Proxy"].strip().lower() == "premium proxy"
    proxy_used = "premium" if is_premium else "regular"

    # build JSON endpoint call
    json_url = raw_url + ".js"
    params   = {"url": json_url, "apikey": API_KEY}
    if is_premium:
        params["premium_proxy"] = "true"
        params["proxy_country"] = "us"

    # fetch with retry
    for attempt in (1, 2):
        try:
            resp = requests.get(ZENROWS_URL, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt == 2:
                with lock:
                    print(f"  → Failed after 2 attempts: {e}")
                return

    # parse variants
    for v in data.get("variants", []):
        # record that we *attempted* this variant
        with lock:
            domain_stats[domain]["checked"] += 1

        # format price
        cents = v.get("price")
        try:
            price = f"${int(cents)/100:,.2f}"
        except Exception:
            # skip price errors
            continue

        # extract & validate barcode
        raw_bar = v.get("barcode")
        if not raw_bar:
            with lock:
                blank_count += 1
            continue

        bar_str = str(raw_bar).strip()
        if not bar_str.isdigit():
            with lock:
                non_numeric_count += 1
            continue

        if len(bar_str) != 12:
            with lock:
                length_count += 1
            continue

        # OK to write
        barcode    = "'" + bar_str
        available  = v.get("available", False)
        variant_id = v.get("id")
        direct_url = f"{raw_url}?variant={variant_id}"

        with lock:
            writer.writerow([direct_url, price, barcode, available, proxy_used])
            domain_stats[domain]["valid"] += 1

# ── RUN THREADPOOL ────────────────────────────────────────────────────────────
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exec:
    for idx, row in enumerate(shopify_rows, 1):
        exec.submit(process_row, idx, row)

f_out.close()

# ── WRITE RESULTS SUMMARY ─────────────────────────────────────────────────────
with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f_res:
    res_writer = csv.writer(f_res)
    res_writer.writerow(["Site", "# Checked", "Valid Output", "Bad Output", "Ratio"])

    for domain, stats in domain_stats.items():
        checked = stats["checked"]
        valid   = stats["valid"]
        bad     = checked - valid
        ratio   = f"{(valid/checked*100):.0f}%" if checked else "0%"
        res_writer.writerow([domain, checked, valid, bad, ratio])

# ── FINAL CONSOLE SUMMARY ─────────────────────────────────────────────────────
print("\nDone.")
print(f" • Total rows in input:         {total_rows}")
print(f" • Shopify rows processed:      {total_shopify}")
print(f" • Non-Shopify rows skipped:    {non_shopify_count}")
print(f" • Output file:                 {OUTPUT_CSV}")
print(f" • Results summary file:        {RESULTS_CSV}")
print(f" • Blank/None barcodes skipped: {blank_count}")
print(f" • Non-numeric barcodes skipped:{non_numeric_count}")
print(f" • Bad-length barcodes skipped: {length_count}")
