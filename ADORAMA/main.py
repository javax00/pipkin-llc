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

write_filename = "final_adorama_" + date_now + ".csv"
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

urls = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def remove_description(json_str):
	# Removes "description": "...", (handles multiline, whitespace, etc)
	# Caution: If description is the last element in the dict, might leave a dangling comma (handle as needed).
	pattern = r'"description":\s*"(?:\\.|[^"\\])*",?\n?'
	return re.sub(pattern, '', json_str, flags=re.DOTALL)

def get_product_links(page):
	global urls
	url = f'https://www.adorama.com/clearance/l/?sel=Filter-By_Specials&perPage=25&startAt={page}'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')
	
	for link in soup.find_all('div', class_='Products_productWr__lP23N'):
		urls.append('https://www.adorama.com/'+link.get('data-sku')+'.html')

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	raw_data = soup.find_all('script', type='application/ld+json')[1].get_text()
	data_json = json.loads(raw_data)

	upc = data_json['gtin12'].strip()
	if len(upc) == 13:
		upc = upc[1:]

	price = data_json['offers'][0]['price']

	with counter_lock:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, link])

if __name__ == "__main__":
	get_products = input('Enter total products: ')

	total_pages = math.ceil(int(get_products)/25)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*25) for i in range(0, total_pages)]
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