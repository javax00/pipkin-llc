import requests
from bs4 import BeautifulSoup
import urllib.parse
import whois
import pandas as pd
import csv
import os
import concurrent.futures
import threading
from concurrent.futures import as_completed

ZENROWS_API_KEY = "ef95565cee4ff7e6df2a9caa8f503da7b988ac2e"
PROMO_KEYWORDS = ["sale", "deal", "clearance", "discount", "promo"]

lock = threading.Lock()  # lock for thread-safe CSV writing

# --- Check if site is Shopify ---
def is_shopify(domain):
	################### NOT SHOPIFY SITE ###################
	xurl = []
	if os.path.exists('NOT_SHOPIFY_SITES.csv'):
		with open('NOT_SHOPIFY_SITES.csv', 'r', encoding='utf-8') as f:
			reader = csv.reader(f)
			for row in reader:
				xurl.append(row)

	for x in xurl:
		if domain in x:
			return False

	################### SHOPIFY SITE ###################
	gurl = []
	if os.path.exists('SHOPIFY_SITES.csv'):
		with open('SHOPIFY_SITES.csv', 'r', encoding='utf-8') as f:
			reader = csv.reader(f)
			for row in reader:
				gurl.append(row)

	for g in gurl:
		if domain in g:
			return True

	try:
		test_url = f"https://{domain}/products.json"
		r = requests.get(test_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
		if r.status_code == 200 and "cdn.shopify.com" in r.text.lower():
			################### SHOPIFY SITE ###################
			with open('SHOPIFY_SITES.csv', 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([domain])
			return True
		################### NOT SHOPIFY SITE ###################
		with open('NOT_SHOPIFY_SITES.csv', 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([domain])
		return False
	except Exception:
		################### NOT SHOPIFY SITE ###################
		with open('NOT_SHOPIFY_SITES.csv', 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([domain])
		return False

# --- Check if site is US-based ---
def is_us_domain(domain):
	try:
		w = whois.whois(domain)
		if w.country and "US" in str(w.country).upper():
			return True
	except Exception:
		pass
	return False

# --- Google search via ZenRows ---
def google_search_upc(upc):
	all_results = []
	dups = []
	for kw in PROMO_KEYWORDS:
		query = f"{upc} {kw} site:.com"
		google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"

		zenrows_url = (
			f"https://api.zenrows.com/v1/?apikey={ZENROWS_API_KEY}"
			f"&url={urllib.parse.quote_plus(google_url)}"
			"&js_render=true&premium_proxy=true&proxy_country=US"
		)

		try:
			resp = requests.get(zenrows_url, timeout=60)
			if resp.status_code != 200:
				print(f"ZenRows error {resp.status_code}")
				continue

			soup = BeautifulSoup(resp.text, "html.parser")

			for g in soup.select("div.tF2Cxc"):
				link = g.select_one("a")["href"] if g.select_one("a") else ""
				domain = urllib.parse.urlparse(link).netloc
				if domain in dups:
					continue
				dups.append(domain)
				if link:
					all_results.append({
						"link": link,
						"domain": domain
					})
		except Exception:
			pass
	return all_results

# --- Worker function for each UPC ---
def process_upc(upc_code, out_file):
	results = google_search_upc(upc_code)

	urls = []
	for r in results:
		if is_shopify(r["domain"]) and is_us_domain(r["domain"]):
			urls.append(r["link"].split('?')[0] + ".json")

	# Save immediately after each UPC
	if urls:
		with lock:
			with open(out_file, "a", newline="", encoding="utf-8") as f:
				writer = csv.writer(f)
				for url in urls:
					writer.writerow([url])

# --- Main ---
if __name__ == "__main__":
	# Read UPCs from KeepaExport-CLEAN.csv
	df = pd.read_csv("KeepaExport-CLEAN.csv", dtype=str)
	if "UPC" not in df.columns:
		raise ValueError("❌ KeepaExport-CLEAN.csv must contain a 'UPC' column")

	upcs = df["UPC"].dropna().unique().tolist()
	total = len(upcs)

	print(f"Total UPCs: {total}")

	out_file = "WEBSITE_JSON.csv"
	# Create CSV with header if not exists
	if not os.path.exists(out_file):
		with open(out_file, "w", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			writer.writerow(["ProductURL"])

	counter = 0

	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		futures = [executor.submit(process_upc, u, out_file) for u in upcs]
		for future in as_completed(futures):
			with lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')