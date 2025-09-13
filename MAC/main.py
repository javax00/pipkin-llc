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

write_filename = "final_mac_" + date_now + ".csv"
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

def get_product_links(url):
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	for item in soup.find('ul', class_='md:max-lg:grid-cols-2').find_all('li', class_='swiper-slide'):
		urls.append('https://www.maccosmetics.com'+item.find('a')['href'])

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	data = soup.find('script', id='page_data').get_text()
	data = json.loads(data)

	for prods in data['consolidated-products']['products']:
		for var in prods['skus']:
			upc = var['UPC_CODE']
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
			price = var['PRICE']
			color = var['SHADE_DESCRIPTION']

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, color, link])

if __name__ == "__main__":
	get_product_links('https://www.maccosmetics.com/deals')
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