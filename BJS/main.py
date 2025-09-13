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

write_filename = "final_bjs_" + date_now + ".csv"
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
	url = f'https://ac.cnstrc.com/browse/group_id/patio-and-garden?c=ciojs-client-2.62.6&key=key_2i36vP8QTs3Ati4x&i=b15e86b9-a699-4312-9060-d5b6e177ad42&s=2&page={page}&num_results_per_page=40&&&fmt_options%5Bhidden_fields%5D=prices.0096&fmt_options%5Bhidden_fields%5D=sale_prices.0096&fmt_options%5Bhidden_fields%5D=original_price.0096&fmt_options%5Bhidden_fields%5D=eligibility.0096&fmt_options%5Bhidden_fields%5D=inventory.0096&fmt_options%5Bhidden_fields%5D=prices.online&fmt_options%5Bhidden_fields%5D=sale_prices.online&fmt_options%5Bhidden_fields%5D=original_price.online&fmt_options%5Bhidden_fields%5D=eligibility.online&fmt_options%5Bhidden_fields%5D=inventory.online&pre_filter_expression=%7B%22or%22%3A%5B%7B%22name%22%3A%22avail_stores%22%2C%22value%22%3A%22online%22%7D%2C%7B%22name%22%3A%22avail_stores%22%2C%22value%22%3A%220096%22%7D%2C%7B%22and%22%3A%5B%7B%22name%22%3A%22avail_stores%22%2C%22value%22%3A%220096%22%7D%2C%7B%22name%22%3A%22avail_sdd%22%2C%22value%22%3A%220096%22%7D%5D%7D%2C%7B%22name%22%3A%22out_of_stock%22%2C%22value%22%3A%22Y%22%7D%5D%7D&_dt=1756791900558'
	html = get_zenrows_html(url)
	soup = json.loads(html)

	for item in soup['response']['results']:
		urls.append('https://www.bjs.com'+item['data']['url'])

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	print(soup.find('div', id='pdp-data'))

	# json_data = soup.find('div', id='pdp-data').find('script').get_text().replace('window.initialPdpData=','').strip()
	# json_data = json.loads(json_data)

	# print(json_data)

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/40)
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

	urls = urls[:2]

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