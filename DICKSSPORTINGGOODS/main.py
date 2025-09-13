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

write_filename = "final_dickssportinggoods_" + date_now + ".csv"
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

partnums = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
	}
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	url = 'https://prod-catalog-product-api.dickssportinggoods.com/v2/search?searchVO={"pageNumber":'+str(page)+',"pageSize":144,"selectedSort":5,"selectedStore":"1419","storeId":"15108","zipcode":"98125","isFamilyPage":true,"mlBypass":false,"snbAudience":"","includeFulfillmentFacets":false,"selectedCategory":"12301_10598220"}'
	html = get_zenrows_html(url)
	data_json = json.loads(html)

	for item in data_json['productVOs']:
		partnums.append(item['parentPartnumber'])

def get_product_info(partnum):
	url = f'https://api-search.dickssportinggoods.com/catalog-productdetails/v4/byPartNumber/15108?id={partnum}&inventory=true&clearance=false'
	html = get_zenrows_html(url)
	json_data = json.loads(html)

	for var in json_data['productsData']['skus']:
		price = var['prices']['offerPrice']
		source_url = 'https://www.dickssportinggoods.com'+var['pdpSeoUrl']
		attr = []
		for vars in var['definingAttributes']:
			attr.append(vars['value'])
		variation = ', '.join(attr)
		for upcs in var['descriptiveAttributes']:
			if upcs['name'] == 'PRIMARY_UPC':
				upc = upcs['value']

		print(upc, price, variation, source_url)

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/144)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(partnums)} product links\n')
	print(partnums[0])
	# partnums = partnums[:1]

	# counter = 0
	# counter_lock = threading.Lock()

	# total = len(partnums)

	# with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
	# 	futures = [executor.submit(get_product_info, partnum) for partnum in partnums]
	# 	for future in as_completed(futures):
	# 		with counter_lock:
	# 			counter += 1
	# 			print(f"Getting product info: {counter} / {total}", end='\r')

	# print('\nDone')