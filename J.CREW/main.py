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

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_jcrew_" + date_now + ".csv"
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

codes = []
final_codes = []
dups = []

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
	global codes
	url = ('https://ac.cnstrc.com/browse/group_id/sale~women?'+
			'c=ciojs-client-2.51.0',
			'&key=key_nu9b76kKatVvDK9C',
			'&i=b53152f4-f18a-48c3-95bb-a1c23563a4d2',
			'&s=3',
			'&page=' + str(page),
			'&num_results_per_page=120',
			'&filters%5Borderable%5D=True',
			'&filters%5BallowedCountries%5D=ALL',
			'&filters%5BallowedCountries%5D=US',
			'&filters%5BisAppExclusive%5D=False',
			'&filters%5BdisplayOn%5D=sale_usd',
			'&variations_map=%7B%22group_by%22%3A%5B%7B%22name%22%3A%22orderable%22%2C%22field%22%3A%22data.orderable%22%7D%2C%7B%22name%22%3A%22productSizingName%22%2C%22field%22%3A%22data.productSizingName%22%7D%2C%7B%22name%22%3A%22color%22%2C%22field%22%3A%22data.color%22%7D%5D%2C%22values%22%3A%7B%22min_price%22%3A%7B%22aggregation%22%3A%22min%22%2C%22field%22%3A%22data.price%22%7D%2C%22max_price%22%3A%7B%22aggregation%22%3A%22max%22%2C%22field%22%3A%22data.price%22%7D%2C%22main_image_url%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.image_url%22%7D%2C%22count%22%3A%7B%22aggregation%22%3A%22field_count%22%2C%22field%22%3A%22data.stockLevel%22%7D%2C%22colorName%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.masterColor%22%7D%2C%22color%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.color%22%7D%2C%22masterColor%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.masterColor%22%7D%2C%22skuShotType%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.skuShotType%22%7D%2C%22min_discount%22%3A%7B%22aggregation%22%3A%22min%22%2C%22field%22%3A%22data.discountValue%22%7D%2C%22max_discount%22%3A%7B%22aggregation%22%3A%22max%22%2C%22field%22%3A%22data.discountValue%22%7D%2C%22badges%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.badges%22%7D%2C%22variation_id%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.variation_id%22%7D%2C%22stockLevel%22%3A%7B%22aggregation%22%3A%22all%22%2C%22field%22%3A%22data.stockLevel%22%7D%2C%22displayOn%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.displayOn%22%7D%2C%22stores%22%3A%7B%22aggregation%22%3A%22first%22%2C%22field%22%3A%22data.stores%22%7D%7D%2C%22dtype%22%3A%22object%22%7D',
			'&_dt=1755595301389')

	html = get_zenrows_html(''.join(url))
	data_json = json.loads(html)
	
	for item in data_json['response']['results']:
		try:
			url = 'https://factory.jcrew.com/m/' + item['data']['defaultCategoryId'].replace('~', '/') + '/' + item['data']['familyId']
			code = item['data']['familyId']
			if code not in codes:
				codes.append([code, url])
		except:
			url = 'https://factory.jcrew.com/p/' + item['data']['defaultCategoryId'].replace('~', '/') + '/' + item['data']['id']
			code = item['data']['id']
			if code not in codes:
				codes.append([code, url])

def get_product_codes(code, source_url):
	global final_codes
	global dups
	url = f'https://factory.jcrew.com/browse/products/{code}?expand=availability%2Cvariations%2Cprices%2Cset_products&display=all&country-code=US'
	html = get_zenrows_html(url)
	json_data = json.loads(html)

	for var in json_data['set_products'][0]['variants']:
		if var['orderable'] == True:
			pid = var['product_id']
			price = var['price']
			
			size = ''
			try:
				size = var['variation_values']['size']
			except:
				pass

			sizename = ''
			try:
				sizename = var['variation_values']['productSizingName']
			except:
				pass

			color = ''
			try:
				color = var['variation_values']['color']
				for c in json_data['set_products'][0]['c_customData']['orderableColors']:
					if c['colorCode'] == color:
						color = c['colorName']
			except:
				color = ''

			v = [color, size, sizename]
			variant = ', '.join(v)

			if pid not in dups:
				dups.append(pid)
				final_codes.append([pid, price, variant, source_url])

def get_product_info(code):
	pid = code[0]

	url = f'https://factory.jcrew.com/browse/products/({pid})?expand=availability%2Cvariations&country-code=US'
	html = get_zenrows_html(url)
	json_data = json.loads(html)

	upc = json_data['data'][0]['c_GTIN']
	price = code[1]
	variant = code[2]
	source_url = code[3]

	with counter_lock:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, variant, source_url])

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

	print(f'\nFound {len(codes)} products\n')



	# codes = codes[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(codes)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_codes, code, url) for code, url in codes]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product codes: {counter} / {total}", end='\r')

	print(f'\nFound {len(final_codes)} product info\n')


	# final_codes = final_codes[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(final_codes)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, code) for code in final_codes]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')