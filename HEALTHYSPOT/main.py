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

write_filename = "final_healthyspot_" + date_now + ".csv"
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

urls = []

def get_zenrows_html(target_url, waitt):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait_for': waitt
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	# url = 'https://healthyspot.com/collections/rawgust'
	# url = 'https://healthyspot.com/collections/primal'
	url = 'https://healthyspot.com/collections/stella-chewys'
	url = f'{url}?page={page}'
	html = get_zenrows_html(url, 'div.boost-sd__product-list')
	soup = BeautifulSoup(html, 'html.parser')

	for item in soup.find('div', class_='boost-sd__product-list').find_all('div', class_='boost-sd__product-item'):
		try:
			code = item.find('b', class_='highlighted-code').text.strip()
		except:
			code = ''
		urls.append(['https://healthyspot.com'+item.find('a')['href'], code])

def get_product_info(link, code):
	html = get_zenrows_html(link+'.json', 'body')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		title = variant['title']

		if len(upc) == 12:
			upc = '0'+upc

		if code == '':
			price = float(variant['price'])
		else:
			price = float(variant['price'])*.8

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, code, link])

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = int(get_pages)
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
		futures = [executor.submit(get_product_info, url, code) for url, code in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')