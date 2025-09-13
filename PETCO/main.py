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
import time
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

write_filename = "final_petco_" + date_now + ".csv"
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
		'js_render': 'true',
		'premium_proxy': 'true',
		# 'proxy_country': 'us',
	}
	r = requests.get(zenrows_api, params=params, timeout=120)
	return r.text

def get_product_links(page):
	# url = f'https://pwcdauseo-zone.cnstrc.com/browse/group_id/25-off-select-freeze-dried-dog-food?c=ciojs-client-2.64.2&key=key_afiSr5Y4gCaaSW5X&i=3c77acd4-156f-45e3-b87e-5b53f28c7e89&s=3&page={page}&num_results_per_page=48&&sort_by=relevance&sort_order=descending&_dt=1755761140191'
	url = f'https://pwcdauseo-zone.cnstrc.com/browse/group_id/dry-dehydrated-dog-food?c=ciojs-client-2.64.2&key=key_afiSr5Y4gCaaSW5X&i=3c77acd4-156f-45e3-b87e-5b53f28c7e89&s=3&page={page}&num_results_per_page=48&&sort_by=relevance&sort_order=descending&_dt=1755767359473'
	html = get_zenrows_html(url)
	data_json = json.loads(html)

	for item in data_json['response']['results']:
		href = 'https://www.petco.com'+item['data']['url']

		with counter_lock:
			urls.append(href)

def get_product_info(link):
	while True:
		try:
			html = get_zenrows_html(link)
			soup = BeautifulSoup(html, 'html.parser')

			script = soup.find('script', id='__NEXT_DATA__').get_text()
			json_data = json.loads(script)

			print(json_data['props']['pageProps']['fragmentRequested'])

			vars = json_data['props']['pageProps']['pageData']['composedItemView']
			for var in vars:
				upc = vars[var]['upcNumber']
				price = vars[var]['price']['price_USD'].replace('$', '')
				variant = vars[var]['defining'][0]['values'][0]['value']
				link = 'https://www.petco.com/shop/en/petcostore/product/'+vars[var]['slug']

				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([upc, price, variant, link])
			break
		except Exception as e:
			time.sleep(10)
			pass

if __name__ == "__main__":
	get_pages = int(input('Enter total prodcts: '))
	total_pages = math.ceil(int(get_pages)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(urls)} product links\n')
	# print(urls[0])

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')