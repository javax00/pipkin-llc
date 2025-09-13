import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
from datetime import datetime
import urllib.parse
import re

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_pureformulas_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variant', 'Promo', 'Source Link']
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

pids = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait': '10000',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	# url = 'https://www.pureformulas.com/brand/protocol-for-life-balance?cio_query=protocol for life balance&cio_options={"resultsPerPage":96,"page":'+str(page)+',"sortBy":"relevance","sortOrder":"descending"}'
	# url = 'https://www.pureformulas.com/search?N=0&Nr=AND(AND(product.brand:Enzymedica,sku-products.tags_:sale080125083125))&Ntt=storefront&Nrpp=96'
	# url = 'https://www.pureformulas.com/brand/now?cio_query=now&cio_options={"resultsPerPage":96,"page":'+str(page)+',"sortBy":"relevance","sortOrder":"descending"}'
	url = 'https://www.pureformulas.com/brand/solaray?cio_query=solaray&cio_options={"resultsPerPage":96,"page":'+str(page)+',"sortBy":"relevance","sortOrder":"descending"}'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	ids = []
	for item in soup.find_all('div', class_='col-sm-3'):
		ids.append(item.get('data-cnstrc-item-id'))
	pids.append(','.join(ids))

def get_product_info(pid):
	url = f'https://www.pureformulas.com/ccstore/v1/skus?skuIds={pid}'
	html = get_zenrows_html(url)
	data_json = json.loads(html)

	
	for item in data_json['items']:
		upc = item['upc_']
		price = item['listPrice']
		price = (float(price)*0.90)*.65
		variant = item['size_variant_option']
		source_link = 'https://www.pureformulas.com' + item['parentProducts'][0]['route']

		promo = 'Code: SOLAR35'

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, variant, promo, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/96)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(pids)} product links\n')
	# print(pids[0])

	# pids = pids[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(pids)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, pid) for pid in pids]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')