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
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_gazellesports_" + date_now + ".csv"
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
	global urls
	# url = f'https://fh4fjd.a.searchspring.io/api/search/search.json?lastViewed=544144&userId=3117e8d9-8f06-42b2-aae4-69ccf09fd0f6&domain=https%3A%2F%2Fgazellesports.com%2Fcollections%2Fall-sale%3Fp%3D2&siteId=fh4fjd&page={page}&resultsPerPage=24&bgfilter.collection_handle=all-sale&redirectResponse=full&resultsFormat=native'
	url = f'https://fh4fjd.a.searchspring.io/api/search/search.json?lastViewed=563363%2C563358%2C544144&userId=%7B%22value%22%3A%7B%22value%22%3A%22%7B%5C%22value%5C%22%3A%7B%5C%22value%5C%22%3A%5C%223117e8d9-8f06-42b2-aae4-69ccf09fd0f6%5C%22%2C%5C%22timestamp%5C%22%3A%5C%222025-08-28T04%3A09%3A39.676Z%5C%22%7D%7D%22%2C%22timestamp%22%3A%222025-08-28T04%3A09%3A40.096Z%22%7D%7D&domain=https%3A%2F%2Fgazellesports.com%2Fcollections%2Fall-sale%3Fp%3D2&siteId=fh4fjd&page={page}&resultsPerPage=24&bgfilter.collection_handle=all-sale&redirectResponse=full&resultsFormat=native'
	html = get_zenrows_html(url)
	
	products = json.loads(html)['results']
	for product in products:
		urls.append('https://gazellesports.com'+product['url'])  

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		if len(upc) >= 13:
			upc = upc[len(upc)-12:len(upc)]
		price = variant['price']
		title = variant['title']

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, link])

if __name__ == "__main__":
	# url = 'https://fh4fjd.a.searchspring.io/api/search/search.json?lastViewed=544144&userId=3117e8d9-8f06-42b2-aae4-69ccf09fd0f6&domain=https%3A%2F%2Fgazellesports.com%2Fcollections%2Fall-sale%3Fp%3D2&siteId=fh4fjd&page=1&resultsPerPage=24&bgfilter.collection_handle=all-sale&redirectResponse=full&resultsFormat=native'
	url = 'https://fh4fjd.a.searchspring.io/api/search/search.json?lastViewed=563363%2C563358%2C544144&userId=%7B%22value%22%3A%7B%22value%22%3A%22%7B%5C%22value%5C%22%3A%7B%5C%22value%5C%22%3A%5C%223117e8d9-8f06-42b2-aae4-69ccf09fd0f6%5C%22%2C%5C%22timestamp%5C%22%3A%5C%222025-08-28T04%3A09%3A39.676Z%5C%22%7D%7D%22%2C%22timestamp%22%3A%222025-08-28T04%3A09%3A40.096Z%22%7D%7D&domain=https%3A%2F%2Fgazellesports.com%2Fcollections%2Fall-sale%3Fp%3D2&siteId=fh4fjd&page=2&resultsPerPage=24&bgfilter.collection_handle=all-sale&redirectResponse=full&resultsFormat=native'
	html = get_zenrows_html(url)
	data_json = json.loads(html)
	total_pages = data_json['pagination']['totalPages']
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

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')