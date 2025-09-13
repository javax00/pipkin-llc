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
import  re

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_shoecarnival_" + date_now + ".csv"
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

pids = []

# def get_zenrows_html(target_url):
# 	params = {
# 		'apikey': ZENROWS_API_KEY,
# 		'url': target_url,
# 		'premium_proxy': 'true',
# 		'proxy_country': 'us',
# 		'js_render': 'true',
# 	}
# 	r = requests.get(zenrows_api, params=params, timeout=90)
# 	return r.text

def get_product_links(page):
	target_url = "https://fa677j9qji-3.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(5.12.0)%3B%20Search%20(5.12.0)%3B%20Browser%3B%20instantsearch.js%20(4.75.4)%3B%20react%20(18.3.1)%3B%20react-instantsearch%20(7.13.7)%3B%20react-instantsearch-core%20(7.13.7)%3B%20JS%20Helper%20(3.22.5)&x-algolia-api-key=a136a668a38bddf37f23208d6293c79c&x-algolia-application-id=FA677J9QJI"

	params = {
		"apikey": ZENROWS_API_KEY,
		"url": target_url,
		"custom_headers": "true",
		"premium_proxy": "true",
		"js_render": "true",
		"proxy_country": "us"
	}

	headers = {
		"content-type": "application/json"
	}

	payload = {
		"requests": [
		{
			"indexName": "production_na02_shoecarnival_demandware_net__shoecarnival__products__default",
			"clickAnalytics": True,
			"facetFilters": [
				["on_sale:true"]
			],
			"facets": ["age", "assignedCategories.id", "brand", "colorPrimary", "gender", "heelHeight", "on_sale", "sizeVariations", "styleType", "widthVariations"],
			"filters": "(assignedCategories.id:\"crocs\")",
			"highlightPostTag": "__/ais-highlight__",
			"highlightPreTag": "__ais-highlight__",
			"hitsPerPage": 23,
			"maxValuesPerFacet": 1000,
			"page": page,
			"query": "",
			"userToken": "abl0w3wrwVxHERlKo1xqYYwXs1"
		}]
	}

	response = requests.post(zenrows_api, params=params, headers=headers, data=json.dumps(payload), timeout=60)
	for item in response.json()['results'][0]['hits']:
		url = 'https://www.shoecarnival.com'+item['url']
		for variant in item['variants_IDs']:
			with counter_lock:
				pids.append([variant, url])

def get_product_info(pid, url, bear):
	target_url = f"https://www.shoecarnival.com/mobify/proxy/api/product/shopper-products/v1/organizations/f_ecom_bkkp_prd/products/{pid}?siteId=shoecarnival"

	params = {
		"apikey": ZENROWS_API_KEY,
		"url": target_url,
		"custom_headers": "true",
		"premium_proxy": "true",
		"js_render": "true",
		"proxy_country": "us"
	}

	headers = {
		"authorization": "Bearer "+bear,
	}

	resp = requests.get(zenrows_api, params=params, headers=headers, timeout=60)
	json_data = resp.json()

	upc = json_data['upc']
	price = json_data['price']
	variantion = f"{json_data['c_size']}, {json_data['c_widthGroup']}, {json_data['c_cgroupPrimary']}"

	with counter_lock:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, variantion, url])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')
	bear = input('input Bearer here: ')

	total_pages = math.ceil(int(get_pages)/24)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(pids)} product ids\n')

	# pids = pids[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(pids)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, pid, url, bear) for pid, url in pids]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')