import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_hobobags_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variant', 'Source Link']
############################# CSV WRITE #################################
script_dir = os.path.dirname(os.path.abspath(__file__))					#
write_csv = os.path.join(script_dir, write_filename)					#
if os.path.exists(write_csv):											#
	os.remove(write_csv)												#
	print(f"Deleted existing file: {write_csv}\nStarting now...\n")		#
																		#
with open(write_csv, 'w', newline='', encoding='utf-8') as f:			#
	writer = csv.writer(f)												#
	writer.writerow(write_headers)										#
############################# CSV WRITE #################################

def get_zenrows_html(target_url):
	# params = {
	# 	'apikey': ZENROWS_API_KEY,
	# 	'url': target_url,
	# 	'premium_proxy': 'true',
	# 	'js_render': 'true',
	# 	'proxy_country': 'us'
	# }
	# r = requests.get(zenrows_api, params=params, timeout=60)
	r = requests.get(target_url, timeout=60)
	return r.text

def get_product_info(page_num):
	global counter

	# url = f'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=982576ff-ca89-4297-b47d-e9c6d21a0a68&uuid=982576ff-ca89-4297-b47d-e9c6d21a0a68&store_id=14420312118&api_type=json&category_id=174444838966&facets_required=1&products_per_page=20&page_num={page_num}&with_product_attributes=true&qs=false'
	url = f'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=982576ff-ca89-4297-b47d-e9c6d21a0a68&uuid=982576ff-ca89-4297-b47d-e9c6d21a0a68&store_id=14420312118&api_type=json&category_id=174444838966&facets_required=1&products_per_page=20&page_num={page_num}&with_product_attributes=true&qs=false'
	html = get_zenrows_html(url)
	data = json.loads(html)

	finals = []
	for product in data['items']:
		if "'alt':" in str(product):
			for var in product['alt']:
				variant = var[0]
				source_url = 'https://www.hobobags.com/collections/sale-leather-handbags-wallets'+var[1]
				upc = var[3]['sku'].split(' ')[1]
				for price in var[3]['att']:
					if 'IN CART!' in str(price):
						price = price[1][0].replace('$', '').replace(' IN CART!', '')
						break
					else:
						price = var[3]['p']

				finals.append([upc, price, variant, source_url])
		else:
			source_url = 'https://www.hobobags.com/collections/sale-leather-handbags-wallets'+product['u']
			for v in product['vra']:
				for i in v[1]:
					if i[0] == 'Barcode':
						upc = i[1][0]
					if i[0] == 'Price':
						price = i[1][0].split(':')[1]
					if i[0] == 'Color':
						variant = i[1][0]

			finals.append([upc, price, variant, source_url])
	for final in finals:
		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow(final)


if __name__ == "__main__":
	# url = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=982576ff-ca89-4297-b47d-e9c6d21a0a68&uuid=982576ff-ca89-4297-b47d-e9c6d21a0a68&store_id=14420312118&api_type=json&category_id=174444838966&facets_required=1&products_per_page=20&page_num=1&with_product_attributes=true&qs=false'
	url = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=982576ff-ca89-4297-b47d-e9c6d21a0a68&uuid=982576ff-ca89-4297-b47d-e9c6d21a0a68&store_id=14420312118&api_type=json&category_id=174444838966&facets_required=1&products_per_page=20&page_num=1&with_product_attributes=true&qs=false'
	html = get_zenrows_html(url)
	data = json.loads(html)
	total_pages = math.ceil(int(data['total_results']) / 21)
	print(f'Found {total_pages} pages\n')

	# total_pages = 1

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, page_num) for page_num in range(1, total_pages + 1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total_pages}", end='\r')

	print('\nDone')
