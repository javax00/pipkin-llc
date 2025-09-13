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

write_filename = "final_mumu_" + date_now + ".csv"
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
	# url = f'https://45ykzl.a.searchspring.io/api/search/search.json?lastViewed=BR2-5337-EM65-XXS%2CMM4-4938-SS69-XS&userId=7a947894-5b99-4b8b-a457-d636a574af62&domain=https%3A%2F%2Fshowmeyourmumu.com%2Fcollections%2Fsale%3Fpage%3D3&sessionId=7eb8b7fb-2af3-4976-9efe-05f8a4893acd&pageLoadId=1cfe905d-df28-4008-8f08-0b74f0093a11&excludedFacets=ss_color_group&siteId=45ykzl&page={page}&intellisuggest=false&bgfilter.ss_exclude=0&bgfilter.ss_app_exclusive=0&bgfilter.ss_bridal_boost=0&bgfilter.collection_id=261439651883&bgfilter.ss_remove_from_collection=0&bgfilter.ss_hidden=0&redirectResponse=full&noBeacon=true&ajaxCatalog=Snap&resultsFormat=native'
	url = f'https://45ykzl.a.searchspring.io/api/search/search.json?lastViewed=MR4-5953-SF27-S%2CMM4-4938-SS69-XS%2CBR2-5337-EM65-XXS&userId=7a947894-5b99-4b8b-a457-d636a574af62&domain=https%3A%2F%2Fshowmeyourmumu.com%2Fcollections%2Fsale%3Fpage%3D3&sessionId=9166b0cc-1a14-4064-899d-e55fcfe1167c&pageLoadId=a9c1be38-0a47-4a1f-ac85-31b62a431d92&excludedFacets=ss_color_group&siteId=45ykzl&page={page}&intellisuggest=false&bgfilter.ss_exclude=0&bgfilter.ss_app_exclusive=0&bgfilter.ss_bridal_boost=0&bgfilter.collection_id=261439651883&bgfilter.ss_remove_from_collection=0&bgfilter.ss_hidden=0&redirectResponse=full&noBeacon=true&ajaxCatalog=Snap&resultsFormat=native'
	html = get_zenrows_html(url)
	data_json = json.loads(html)

	for item in data_json['results']:
		urls.append(item['url'])

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = variant['price']
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

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
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')