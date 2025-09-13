# pip install requests
import csv
import requests
import os
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# ── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_CSV         = "P1 Product Links.csv"
OUTPUT_CSV        = "P2 UPC Check.csv"
RESULTS_CSV       = "P2 UPC Check results.csv"
ZENROWS_URL       = "https://api.zenrows.com/v1/"
API_KEY           = ""
MAX_WORKERS       = 20
TIMEOUT           = 60  # seconds per request attempt

# ── LOAD INPUT ────────────────────────────────────────────────────────────────
with open(INPUT_CSV, newline="", encoding="utf-8") as f_in:
    reader        = csv.DictReader(f_in)
    product_rows  = list(reader)

total_rows = len(product_rows)
if total_rows == 0:
    print("No product links found.")
    exit()

# ── CLEAN UP OLD OUTPUTS ───────────────────────────────────────────────────────
for fn in (OUTPUT_CSV, RESULTS_CSV):
    if os.path.exists(fn):
        os.remove(fn)

lock = threading.Lock()

# overall invalid counters (for console summary)
blank_count       = 0
non_numeric_count = 0
length_count      = 0

# domain‐level stats
domain_stats = defaultdict(lambda: {"checked": 0, "valid": 0})

# ── SET UP MAIN OUTPUT ────────────────────────────────────────────────────────
f_out = open(OUTPUT_CSV, "w", newline="", encoding="utf-8")
writer = csv.writer(f_out)
writer.writerow([
    "Variant URL",
    "Price",
    "Barcode",
    "Available"
])

def process_row(idx, row):
    global blank_count, non_numeric_count, length_count

    raw_url = row["product_link"].strip().rstrip("/")
    parsed  = urlparse(raw_url)
    domain  = parsed.netloc.lower()

    with lock:
        print(f"Processing Url {idx} of {total_rows} ({domain})")

    # build JSON endpoint call
    json_url = raw_url + ".js"
    params   = {"url": json_url, "apikey": API_KEY}

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
        with lock:
            domain_stats[domain]["checked"] += 1

        # format price
        cents = v.get("price")
        try:
            price = f"${int(cents)/100:,.2f}"
        except Exception:
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
            writer.writerow([direct_url, price, barcode, available])
            domain_stats[domain]["valid"] += 1

# ── RUN THREADPOOL ────────────────────────────────────────────────────────────
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exec:
    for idx, row in enumerate(product_rows, 1):
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
print(f" • Output file:                 {OUTPUT_CSV}")
print(f" • Results summary file:        {RESULTS_CSV}")
print(f" • Blank/None barcodes skipped: {blank_count}")
print(f" • Non-numeric barcodes skipped:{non_numeric_count}")
print(f" • Bad-length barcodes skipped: {length_count}")