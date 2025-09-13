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

write_filename = "final_nhc_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Promo', 'Variant', 'Source Link']
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
		'wait': '5000'
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	url = (
		'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss'
		'?c=4902918'
		'&commercecategoryurl=%2Fbrand%2Fnow-foods'
		'&consultLevel=0'
		'&country=US'
		'&custitem_is_nhc_item=true'
		'&custitem_nhc_hide_from_website=false'
		'&domain=www.nhc.com%2Fbrand%2Fnow-foods'
		'&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website'
		'&fieldset=search'
		'&include=facets'
		'&isloggedin=false'
		'&language=en'
		'&limit=72'
		'&matrixchilditems_fieldset=matrixchilditems_search'
		'&model=facetsModel'
		'&n=3'
		f'&offset={page}'
		'&postman=false'
		'&priceLevelIds%5Bemployee%5D=4'
		'&priceLevelIds%5Bguest%5D%5Blist%5D=8'
		'&priceLevelIds%5Bguest%5D%5Bselling%5D=7'
		'&priceLevelIds%5Bmember%5D%5Blist%5D=10'
		'&priceLevelIds%5Bmember%5D%5Bselling%5D=9'
		'&priceLevelIds%5Bretail%5D%5Blist%5D=12'
		'&priceLevelIds%5Bretail%5D%5Bselling%5D=11'
		'&pricelevel=7'
		'&sort=commercecategory%3Adesc'
		'&ss_sessionId=81847679-7a38-45a7-a661-6ea0c178ac9b'
		'&ss_siteId=y11w6k'
		'&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390'
		'&use_pcv=T'
	)

	html = get_zenrows_html(url)
	json_data = json.loads(html)

	for item in json_data['items']:
		url = 'https://www.nhc.com'+item['_url']
		if 'matrixchilditems_detail' in str(item):
			for i in item['matrixchilditems_detail']:
				name = item['custitem_nhc_brand'] + ' ' + item['storedisplayname2']
				price = i['onlinecustomerprice']
				variant = i['custitem_nhc_matrix_size_option']
				name = name + ' ' + variant

				urls.append([price, name, variant, url])
		else:
			name = item['custitem_nhc_brand'] + ' ' + item['storedisplayname2']
			price = item['onlinecustomerprice']
			variant = ''

			urls.append([price, name, variant, url])

def get_product_info(price, name, variant, url):
	target_url = f"https://api.upcitemdb.com/prod/trial/search?s={name}"
	html = get_zenrows_html(target_url)
	data_json =	json.loads(html)

	if 'RESP002' not in html:
		for item in data_json["items"]:
			with counter_lock:
				price = float(price)*.85
				promo =  'NOW15'
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([item['ean'], price, promo, variant, url])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/72)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*72) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(urls)} product links\n')

	# urls = urls[:1]

	# counter = 0
	# counter_lock = threading.Lock()

	# total = len(urls)

	# with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
	# 	futures = [executor.submit(get_product_info, price, name, variant, url) for price, name, variant, url in urls]
	# 	for future in as_completed(futures):
	# 		with counter_lock:
	# 			counter += 1
	# 			print(f"Getting product info: {counter} / {total}", end='\r')

	# print('\nDone')
