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

write_filename = "final_bomgaars_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Source Link']
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

infos = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait_for': 'ol.products',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	global infos
	url = f'https://www.bomgaars.com/sale-items.html?p={page}&product_list_limit=32'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')
	
	products = soup.find('ol', class_='products').find_all('li', class_='product-item')
	for product in products:
		name = product.find('a').get('title')
		source_url = product.find('a').get('href')
		price = product.find('span', {'class': 'price-wrapper', 'data-price-type': 'finalPrice'}).get('data-price-amount')

		infos.append([name, price, source_url])

def get_product_info(info):
	target_url = f"https://api.upcitemdb.com/prod/trial/search?s={info[0]}"

	params = {
		'url': target_url,
		'apikey': ZENROWS_API_KEY,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'wait': '3000',
	}

	r = requests.get(zenrows_api, params=params, timeout=60)

	if 'RESP002' not in r.text:
		data = r.json()
		for item in data["items"]:
			upc = item['ean']
			price = info[1]
			source_url = info[2]

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, source_url])


if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/32)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(infos)} product links\n')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(infos)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, info) for info in infos]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')