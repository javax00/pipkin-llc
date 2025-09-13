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

write_filename = "final_rothys_" + date_now + ".csv"
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

urls = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
	}
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	url = f'https://ac.cnstrc.com/browse/group_id/final-few?c=ciojs-client-bundled-2.55.0&key=key_JkH9ZgDJ7wywqcNO&i=3a462f91-264a-4649-a070-4a0dae4a0b21&s=2&us=US&page={page}&num_results_per_page=100&&sort_by=relevance&sort_order=descending&fmt_options%5Bhidden_fields%5D=price_US&fmt_options%5Bhidden_fields%5D=compareprice_US&fmt_options%5Bhidden_fields%5D=colorCountByMarket.US&fmt_options%5Bhidden_facets%5D=price_US&pre_filter_expression=%7B%22and%22%3A%5B%7B%22name%22%3A%22published%22%2C%22value%22%3A%22True%22%7D%2C%7B%22name%22%3A%22countries_published%22%2C%22value%22%3A%22US%22%7D%5D%7D&_dt=1756878651176'
	html = get_zenrows_html(url)
	data = json.loads(html)

	for item in data['response']['results']:
		urls.append(item['data']['url'])

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		if not upc.isdigit():
			upc = ''
		elif len(upc) <= 10:
			upc = ''
		elif len(upc) == 11:
			upc = '00'+upc
		elif len(upc) == 12:
			upc = '0'+upc
		elif len(upc) == 14:
			upc = upc[1:]
		price = variant['price']
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/100)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(urls)} product links\n')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')