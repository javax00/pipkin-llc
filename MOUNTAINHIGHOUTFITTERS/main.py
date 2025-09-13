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

write_filename = "final_mountainhighoutfitters_" + date_now + ".csv"
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
        'wait': '2000',
	}
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	# url = f'https://85m9ls.a.searchspring.io/api/search/search.json?lastViewed=502556&userId=fa5e1a4f-a9d4-459c-8dc9-a66261b20d0b&domain=https://mountainhighoutfitters.com/collections/sale?page={page}&sessionId=09541dfa-c5b8-4510-afbf-06971d2140af&pageLoadId=c778b56e-7f37-4cf8-a143-89009f5c8f51&siteId=85m9ls&page={page}&resultsPerPage=51&bgfilter.collection_handle=sale&redirectResponse=full&ajaxCatalog=Snap&resultsFormat=native'
	url = f'https://85m9ls.a.searchspring.io/api/search/search.json?lastViewed=502556%2C472544&userId=fa5e1a4f-a9d4-459c-8dc9-a66261b20d0b&domain=https%3A%2F%2Fmountainhighoutfitters.com%2Fcollections%2Fsale%3Fpage%3D{page}&sessionId=c6e18b72-6ade-4454-8bf7-c1a8f30791c7&pageLoadId=559f44a8-290b-4525-a761-4538831f5e35&siteId=85m9ls&page={page}&resultsPerPage=51&bgfilter.collection_handle=sale&redirectResponse=full&ajaxCatalog=Snap&resultsFormat=native'
	html = get_zenrows_html(url)
	data_json = json.loads(html)

	for item in data_json['results']:
		urls.append('https://mountainhighoutfitters.com'+item['url'])

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = variant['price']
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/51)
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