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

write_filename = "final_boscovs_" + date_now + ".csv"
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

skus = []

def get_product_links(page, pathid, cookie):
	global skus
	TARGET_URL = (
		"https://search.unbxd.io/e01284e312492ace50b6cadeb566e72d/boscovs-com811221579175852/category"
		f"?p-id=categoryPathId%3A%{pathid}%22"
		"&facet.multiselect=true"
		"&variants=true"
		"&variants.fields=title,v_imageUrl"
		"&variants.count=1"
		"&variants.groupBy=price"
		"&fields=name,isbundle,uniqueId,price_min,boscovsexclusive,madeinusa,more_colors_available,was_price_min,imageUrl,productUrl,rating,numberreviews,saleBadge,sku,styleCode,hoverImageUrl,maxLinenLoverPrice,price_max,was_price_max,promotion_message,alternate_images"
		"&spellcheck=true"
		"&pagetype=boolean"
		"&rows=36"
		f"&start={page}"
		"&version=V2"
		"&uc_param=undefined"
		"&viewType=GRID"
		"&facet.version=V2"
	)

	params = {
		"apikey": ZENROWS_API_KEY,
		"url": TARGET_URL,
		"custom_headers": "true",
		"premium_proxy": "true",
		"proxy_country": "us",
	}

	headers = {
		"accept": "application/json, */*",
		"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
					"AppleWebKit/537.36 (KHTML, like Gecko) "
					"Chrome/139.0.0.0 Safari/537.36",
		# Cloudflare cookie is often ephemeral; keep only if required
		"Cookie": cookie,
	}

	# resp = requests.get(zenrows_api, params=params, headers=headers, timeout=60)
	resp = requests.get(TARGET_URL, headers=headers, timeout=60)
	resp_json = resp.json()

	for item in resp_json['response']['products']:
		with counter_lock:
			skus.append([item['sku'], item['price_min'], item['productUrl']])

def get_product_info(code):
	TARGET_URL = (
		"https://api.bazaarvoice.com/data/batch.json?passkey=dgg6hwujumf0l4tfynv1d9adr"
		"&apiversion=5.5"
		"&displaycode=6514-en_us"
		"&resource.q0=products"
		f"&filter.q0=id%3Aeq%3A{code[0]}"
		"&stats.q0=reviews"
		"&filteredstats.q0=reviews"
		"&filter_reviews.q0=contentlocale%3Aeq%3Aen_US"
		"&filter_reviewcomments.q0=contentlocale%3Aeq%3Aen_US"
		"&resource.q1=reviews"
		"&filter.q1=isratingsonly%3Aeq%3Afalse"
		f"&filter.q1=productid%3Aeq%3A{code[0]}"
		"&filter.q1=contentlocale%3Aeq%3Aen_US"
		"&sort.q1=submissiontime%3Adesc"
		"&stats.q1=reviews"
		"&filteredstats.q1=reviews"
		"&include.q1=authors%2Cproducts%2Ccomments"
		"&filter_reviews.q1=contentlocale%3Aeq%3Aen_US"
		"&filter_reviewcomments.q1=contentlocale%3Aeq%3Aen_US"
		"&filter_comments.q1=contentlocale%3Aeq%3Aen_US"
		"&limit.q1=8"
		"&offset.q1=0"
		"&limit_comments.q1=3"
		"&resource.q2=reviews"
		f"&filter.q2=productid%3Aeq%3A{code[0]}"
		"&filter.q2=contentlocale%3Aeq%3Aen_US"
		"&limit.q2=1"
		"&resource.q3=reviews"
		f"&filter.q3=productid%3Aeq%3A{code[0]}"
		"&filter.q3=isratingsonly%3Aeq%3Afalse"
		"&filter.q3=issyndicated%3Aeq%3Afalse"
		"&filter.q3=rating%3Agt%3A3"
		"&filter.q3=totalpositivefeedbackcount%3Agte%3A3"
		"&filter.q3=contentlocale%3Aeq%3Aen_US"
		"&sort.q3=totalpositivefeedbackcount%3Adesc"
		"&include.q3=authors%2Creviews%2Cproducts"
		"&filter_reviews.q3=contentlocale%3Aeq%3Aen_US"
		"&limit.q3=1"
		"&resource.q4=reviews"
		f"&filter.q4=productid%3Aeq%3A{code[0]}"
		"&filter.q4=isratingsonly%3Aeq%3Afalse"
		"&filter.q4=issyndicated%3Aeq%3Afalse"
		"&filter.q4=rating%3Alte%3A3"
		"&filter.q4=totalpositivefeedbackcount%3Agte%3A3"
		"&filter.q4=contentlocale%3Aeq%3Aen_US"
		"&sort.q4=totalpositivefeedbackcount%3Adesc"
		"&include.q4=authors%2Creviews%2Cproducts"
		"&filter_reviews.q4=contentlocale%3Aeq%3Aen_US"
		"&limit.q4=1"
		"&callback=BV._internal.dataHandler0"
	)

	params = {
		"apikey": ZENROWS_API_KEY,
		"url": TARGET_URL,
		"premium_proxy": "true",
		"proxy_country": "us"
	}

	# response = requests.get(zenrows_api, params=params, timeout=60)
	response = requests.get(TARGET_URL, timeout=60)

	data = response.text.replace('BV._internal.dataHandler0(', '').replace(')', '')
	for upc in json.loads(data)['BatchedResults']['q0']['Results'][0]['UPCs']:

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, code[1], 'https://www.boscovs.com'+code[2]])

if __name__ == "__main__":
	print('Get from POSTMAN')
	get_products = input('Enter total products: ')
	get_pathid = input('Enter path id: ')
	get_cookie = input('Enter cookie: ')

	total_pages = math.ceil(int(get_products)/36)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*36, get_pathid, get_cookie) for i in range(0, total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(skus)} product links')
	# print(skus[0])

	counter = 0
	counter_lock = threading.Lock()

	total = len(skus)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, sku) for sku in skus]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')