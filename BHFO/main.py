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
import time

urls = []

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_bhfo_" + date_now + ".csv"
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
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us'
	}
	r = requests.get(zenrows_api, params=params, timeout=60)
	return r.text

def get_product_links(page):
	global urls
	url = f'https://twxmeg.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=twxmeg&domain=https://www.bhfo.com/collections/half-off&bgfilter.collection_id=310978773162&q=&userId=a0878782-8327-42aa-86ac-10b5f70bd6f1&sessionId=035e5536-e67f-4e38-8d23-6bd91edf8415&pageLoadId=0d8a255e-53a3-4477-aa44-6931c3c6eb46&page={page}&lastViewed=BH5213876&lastViewed=BH6215967&lastViewed=BH6102497&lastViewed=BH6225862&lastViewed=BH4594199&lastViewed=BH4594543&lastViewed=BH6227148'
	html = get_zenrows_html(url)
	data = json.loads(html)
	for product in data['results']:
		with counter_lock:
			link = product['url']
			urls.append(link)

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = variant['price']
		title = variant['title']
		source_url = link+'?variant='+str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_url])

if __name__ == "__main__":
	url = 'https://twxmeg.a.searchspring.io/api/search/search.json?ajaxCatalog=v3&resultsFormat=native&siteId=twxmeg&domain=https://www.bhfo.com/collections/half-off&bgfilter.collection_id=310978773162&q=&userId=a0878782-8327-42aa-86ac-10b5f70bd6f1&sessionId=035e5536-e67f-4e38-8d23-6bd91edf8415&pageLoadId=0d8a255e-53a3-4477-aa44-6931c3c6eb46&page=1&lastViewed=BH5213876&lastViewed=BH6215967&lastViewed=BH6102497&lastViewed=BH6225862&lastViewed=BH4594199&lastViewed=BH4594543&lastViewed=BH6227148'
	html = get_zenrows_html(url)
	data = json.loads(html)
	total_pages = data['pagination']['totalPages']
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\n\nFound {len(urls)} product links')

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')