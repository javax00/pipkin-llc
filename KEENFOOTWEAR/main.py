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

write_filename = "final_keenfootwear_" + date_now + ".csv"
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
	url = f'https://rr5nnm.a.searchspring.io/api/search/search.json?lastViewed=195208776496%2C195208821929&userId=bc3aa223-97af-4c24-8f4d-8bada51b1a7b&domain=https%3A%2F%2Fwww.keenfootwear.com%2Fcollections%2Fsale%3Fview%3Dproducts%26ppage%3D{page}&sessionId=457f6f3f-2815-4b05-af11-849bfb01c505&pageLoadId=c86ce261-dc7a-4fdc-b8a9-8e762175d06d&siteId=rr5nnm&page=2&bgfilter.ss_is_published=1&bgfilter.collection_handle=sale&noBeacon=true&ajaxCatalog=Snap&resultsFormat=native'
	html = get_zenrows_html(url)
	data = json.loads(html)

	for item in data['results']:
		urls.append('https://www.keenfootwear.com'+item['url'])

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

	total_pages = math.ceil(int(get_pages)/60)
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
	print(urls[0])

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