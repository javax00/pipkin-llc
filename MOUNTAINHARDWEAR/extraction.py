import csv
import os
import requests
import json
from dotenv import load_dotenv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
zenrows_api_key = os.getenv('ZENROWS_API_KEY')
if not zenrows_api_key:
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")

zenrows_url = "https://api.zenrows.com/v1/"
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'product_url.csv')
final_csv = os.path.join(script_dir, 'final_mountainhardwear.csv')

if os.path.exists(final_csv):
	os.remove(final_csv)
	print(f"Deleted existing file: {final_csv}")

products = []
with open(csv_file, 'r', encoding='utf-8') as f:
	reader = csv.reader(f)
	header = next(reader)
	for row in reader:
		products.append(row)

# products = products[:2]

csv_lock = threading.Lock()
count_lock = threading.Lock()
working_count = 0

def process_product(product):
	global working_count
	with count_lock:
		working_count += 1
		print(f"Currently processing products: {working_count}/{len(products)}")

	colors = product[0].split('_')
	target_url = product[1]
	params = {
		"apikey": zenrows_api_key,
		"url": target_url,
		"js_render": "true",
		"premium_proxy": "true",
		"proxy_country": "ca"
	}
	try:
		r = requests.get(zenrows_url, params=params, timeout=60)
	except Exception as e:
		print(f"Request failed for {target_url}: {e}")
		with count_lock:
			print(1)
			working_count -= 1
		return

	if r.status_code != 200:
		print(f"Request failed for {target_url}: {r.status_code} {r.text[:200]} ...")
		with count_lock:
			print(2)
			working_count -= 1
		return

	try:
		data = r.json()
		for color in colors:
			for x in data['product']['variationAttributes'][0]['values']:
				if x['displayValue'] == color:
					if x['selectable'] == True and x['masterSelectable'] == True:
						for y in data['product']['variantData']:
							if data['product']['variantData'][y]['color'] == x['id']:
								upc = f"'{y}"
								price = x['salesPrice']['value']
								variant = f"{x['displayValue']} - {data['product']['variantData'][y]['size']}"
								source_link = x['pdpUrl']

								with csv_lock:
									with open(final_csv, 'a', newline='', encoding='utf-8') as f_csv:
										writer = csv.writer(f_csv)
										writer.writerow([upc, price, variant, source_link])
	except Exception:
		print("Not a JSON response. Here is the start of the response:")
		print(target_url)

with open(final_csv, 'w', newline='', encoding='utf-8') as f_csv:
	writer = csv.writer(f_csv)
	writer.writerow(['UPC', 'Price', 'Variant', 'Source Link'])

with ThreadPoolExecutor(max_workers=15) as executor:
	executor.map(process_product, products)

print('Extraction Complete!')