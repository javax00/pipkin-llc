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

write_filename = "final_charmcityrun_" + date_now + ".csv"
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

main_prod_id = []
var_prod_id = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_id_main(page_num):
	global main_prod_id
	target_url = "https://shop.charmcityrun.com/api/products"

	payload = json.dumps({
	"brand": -1,
	"category": -1,
	"collection": -1,
	"search": "",
	"grouped": True,
	"size": 36,
	"cost": -1,
	"page": page_num,
	"stock": -1,
	"complete": -1,
	"live": -1,
	"sort": "brandName, name",
	"sortType": "asc",
	"admin": False,
	"instore": False,
	"onsale": False,
	"shipable": False,
	"sizes": [],
	"widths": []
	})

	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
	}

	headers = {
		'content-type': 'application/json'
	}

	response = requests.post(
		zenrows_api,
		params=params,
		headers=headers,
		data=payload,
		timeout=60
	)

	response_json = response.json()

	for data in response_json['data']:
		main_prod_id.append(data['productId'])

def get_product_var_ids(prod_id):
	global var_prod_id
	target_url = "https://shop.charmcityrun.com/api/product"

	payload = json.dumps({"id":prod_id})

	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
	}

	headers = {
		'content-type': 'application/json'
	}

	response = requests.post(
		zenrows_api,
		params=params,
		headers=headers,
		data=payload,
		timeout=60
	)

	response_json = response.json()

	for data in response_json['colors']:
		var_prod_id.append([data['sku'], data['productId'], data['color'], 'https://shop.charmcityrun.com/product/'+str(data['productId'])+'/'+str(data['brandName'])])

		




def get_final_data(prod_id):
	global var_prod_id
	target_url = "https://shop.charmcityrun.com/api/options"

	payload = json.dumps({"sku":prod_id[0],"id":prod_id[1],"relay":-1})

	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
	}

	headers = {
		'content-type': 'application/json'
	}

	response = requests.post(
		zenrows_api,
		params=params,
		headers=headers,
		data=payload,
		timeout=60
	)

	response_json = response.json()

	for data in response_json['data']:
		if data['inventory'] != []:
			for inv in data['inventory']:
				upc = inv['upc']
				price = inv['cost']
				variant = prod_id[2]
				source_link = prod_id[3]

				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([upc, price, variant, source_link])
	
	if response_json['unassigned'] != []:
		for data in response_json['unassigned']:
			upc = data['upc']
			price = data['cost']
			variant = prod_id[2]
			source_link = prod_id[3]

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, variant, source_link])











if __name__ == "__main__":
	get_products = input('Enter total pages: ')

	total_pages = int(get_products)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_id_main, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting main product id: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(main_prod_id)} product main id\n')
	




	counter = 0
	counter_lock = threading.Lock()

	# main_prod_id = main_prod_id[:1]

	total = len(main_prod_id)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_var_ids, prod_id) for prod_id in main_prod_id]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting variation ids: {counter} / {total}", end='\r')

	print(f'\n\nFound {len(var_prod_id)} product variation ids')






	counter = 0
	counter_lock = threading.Lock()

	# var_prod_id = var_prod_id[:1]

	total = len(var_prod_id)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_final_data, final_id) for final_id in var_prod_id]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting final data: {counter} / {total}", end='\r')

	print('\nDone.')