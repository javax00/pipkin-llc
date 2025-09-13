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

write_filename = "final_heartratemonitorsusa_" + date_now + ".csv"
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
		'wait_for': 'div.boost-sd__product-list',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_info(page):
	global urls

	target_url = ("https://services.mybcapps.com/bc-sf-filter/filter?t=1754994968914"
	"&_=pf"
	"&shop=heartratemonitorsusa.myshopify.com"
	f"&page={page}"
	"&limit=24"
	"&sort=title-ascending"
	"&locale=en"
	"&event_type=init"
	"&build_filter_tree=true"
	"&sid=b615f2ef-efcf-4934-b764-936cb74a32a0"
	"&pg=collection_page"
	"&zero_options=true"
	"&product_available=false"
	"&variant_available=false"
	"&sort_first=available"
	"&urlScheme=2"
	"&collection_scope=0"
	"&collectionId=0"
	"&handle=all")

	zenrows_url = "https://api.zenrows.com/v1/"
	params = {"apikey": ZENROWS_API_KEY, "url": target_url}

	response = requests.get(zenrows_url, params=params, timeout=60)
	
	for product in response.json()['products']:
		source_link = 'https://www.heartratemonitorsusa.com/products/'+product['handle']
		for info in product['variants']:
			upc = info['barcode']
			price = info['price']
			title = info['title']

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/24)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\n\nDone\n')