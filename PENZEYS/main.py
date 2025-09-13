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

write_filename = "final_penzeys_" + date_now + ".csv"
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

def get_zenrows_html(target_url, waitt):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait_for': waitt,
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(letter):
	url = f'https://www.penzeys.com/shop/spices/?letter={letter}'
	html = get_zenrows_html(url, 'div.template-col')
	soup = BeautifulSoup(html, 'html.parser')

	for item in soup.find('div', class_='template-col').find_all('div', class_='template-tile'):
		name = 'Penzeys ' + item.find('h3').text
		source_link = 'https://www.penzeys.com'+item.find('a').get('href')
		for sel in item.find('select').find_all('option'):
			# var = sel.text.split(' ')[1]
			price = sel.text.split('$')[1]

			with counter_lock:
				urls.append([name, price, source_link])

def get_product_info(name, price, link):
	html = get_zenrows_html(f'https://api.upcitemdb.com/prod/trial/search?s={name}', 'body')
	data = json.loads(html)

	if 'RESP002' not in str(data):
		for upc in data["items"]:
			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc["ean"], price, link])

if __name__ == "__main__":
	letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
	# letters = ['A']

	# Counter for progress
	counter = 0
	counter_lock = threading.Lock()  # Lock to synchronize access to the counter
	total = len(letters)

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(get_product_links, letter) for letter in letters]
		for future in concurrent.futures.as_completed(futures):
			with counter_lock:  # Ensure thread-safe access to the counter
				counter += 1
				print(f"Getting letter: {counter} / {total}", end='\r')  # Print progress

	print(f'\nFound {len(urls)} product links\n')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, name, price, link) for name, price, link in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')