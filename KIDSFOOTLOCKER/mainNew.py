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
import time
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

write_filename = "final_tacticalgear_" + date_now + ".csv"
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
ids = []

def get_product_links(page):
	url = f"https://www.kidsfootlocker.com/zgw/search-core/products/v3/search?query=%3A%3Acollection_id%3Asale&q=Sale&currentPage={page}&sort=relevance&pageSize=48&pageType=browse&timestamp=4"

	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'x-kpsdk-ct': '0bQOJKkiXRD4KQYMkqMxOuZHY5AokxymcZcPSW2mU5BtSGROPhM5rWlnboEXJN6MUDTK7Vtg23AgTLClgVZcWU8EO7VHZ0zcR24CUSMqiOx9PwQJuyJ7uneJFUSUyyZzPxnDNWTDJKdxEZgq7RpfxTSiMTZ7Oyc5dD2aEyupQoc',
		'Cookie': 'KP_UIDz=0aGE2G59hhNd2qxdq66fXhLE7A9MB0xrkO0IABsNVeksxSQeEHbsS8eBKJ9N6uR5kIYjYdKnn5DgmkoMeFASORPzD5xIdS74IkmEK6AHBjsAjPnkOYPrTyybu92evAby3LaatxQfwrlSFJ8ErzQLd2niYFmkRXeM9CAUbjVmeWM; KP_UIDz-ssn=0aGE2G59hhNd2qxdq66fXhLE7A9MB0xrkO0IABsNVeksxSQeEHbsS8eBKJ9N6uR5kIYjYdKnn5DgmkoMeFASORPzD5xIdS74IkmEK6AHBjsAjPnkOYPrTyybu92evAby3LaatxQfwrlSFJ8ErzQLd2niYFmkRXeM9CAUbjVmeWM'
	}

	response = requests.get(url, headers=headers)

	for item in response.json()['products']:
		price = item['price']['value']
		source_url = f'https://www.kidsfootlocker.com/product/~/{item['baseProduct']}.html'

		infos.append([source_url, price])

def get_product_info(url, price):
	print(url)
	response = requests.get(url, timeout=90)
	time.sleep(5)
	# print(response.text[:10])
	soup = BeautifulSoup(response.text, 'html.parser')

	print(soup.find('div', {'data-bv-show': 'rating_summary'}).get('data-bv-product-id'))
		
if __name__ == "__main__":
	get_products = input('Enter total products: ')

	total_pages = math.ceil(int(get_products)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(infos)} product links\n')

	# infos = infos[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(infos)

	with ThreadPoolExecutor(max_workers=1) as executor:
		futures = [executor.submit(get_product_info, url, price) for url, price in infos]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				# print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')