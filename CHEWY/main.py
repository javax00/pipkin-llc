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

write_filename = "final_chewy_" + date_now + ".csv"
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

def get_zenrows_html(target_url, timew):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait': timew,
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	url = f'https://www.chewy.com/plp/api/search?catalogId=1006&count=36&from={page}&sort=byRelevance&groupId=2723'
	html = get_zenrows_html(url, '100')
	data_json = json.loads(html)

	for item in data_json['products']:
		href = item['href']

		with counter_lock:
			urls.append(href)

def get_product_info(link):
	while True:
		try:
			html = get_zenrows_html(link, '10000')
			soup = BeautifulSoup(html, 'html.parser')

			script = soup.find('script', {'type': 'application/ld+json'}).get_text()
			json_data = json.loads(script)
			
			final = []
			if 'hasVariant' in script:
				for var in json_data['hasVariant']:
					if '"gtin13":' in script:
						upc = var['gtin13']
					elif '"gtin12":' in script:
						upc = var['gtin12']
					else:
						upc = ''

					if upc.isdigit() == False: 
						upc = ''

					price = var['offers'][0]['price']

					variant = ''
					if '"size":' in script:
						variant = var['size']
					elif '"count":' in script:
						variant = var['count']
					elif '"color":' in script:
						variant = var['color']

					final.append([upc, price, variant, link])
			else:
				if '"gtin13":' in script:
					upc = json_data['gtin13']
				elif '"gtin12":' in script:
					upc = json_data['gtin12']
				else:
					upc = ''

				if upc.isdigit() == False: 
					upc = ''

				price = json_data['offers']['price']

				variant = ''
				if '"size":' in script:
					variant = json_data['size']
				elif '"count":' in script:
					variant = json_data['count']
				elif '"color":' in script:
					variant = json_data['color']

				final.append([upc, price, variant, link])

			for fo in final:
				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow(fo)
			break
		except:
			pass

if __name__ == "__main__":
	get_pages = int(input('Enter total prodcts: '))
	total_pages = math.ceil(int(get_pages)/36)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(0, get_pages, 36)]
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

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')