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

write_filename = "final_obozfootwear_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Color', 'Source Link']
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
		'js_render': 'true'
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	global urls
	url = f'https://obozfootwear.com/en-us/category/sale?page={page}'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')
	
	for item in soup.find_all('li', class_='product-card'):
		urls.append('https://obozfootwear.com'+item.find('a')['href'])


def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	price = soup.find('span', class_='sale-price').text.replace('$', '').strip()
	color = soup.find('div', class_='selected-label').find('span').text.strip()

	for script in soup.find_all('script'):
		if 'window.__NUXT__=' in script.get_text():
			for upc in re.findall(r'(?<!\d)\d{12}(?!\d)', script.get_text()):
				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([upc, price, color, link])
			break


if __name__ == "__main__":
	get_products = input('Enter total products: ')

	total_pages = math.ceil(int(get_products)/32)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
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