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
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_dtlr_" + date_now + ".csv"
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

def get_zenrows_html(target_url):
	# params = {
	# 	'apikey': ZENROWS_API_KEY,
	# 	'url': target_url,
	# 	'premium_proxy': 'true',
	# 	'js_render': 'true',
	# 	'proxy_country': 'us'
	# }
	# r = requests.get(zenrows_api, params=params, timeout=60)
	r = requests.get(target_url, timeout=60)
	return r.text

def get_product_info(page_num, total_pages):
	global counter

	# url = f'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=151002447951&facets_required=1&products_per_page=21&page_num={page_num}&with_product_attributes=true&spv=%7B%228542653317354%22:1753871179%7D&st=undefined&qs=false'
	# url = f'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=442884227306&facets_required=1&products_per_page=21&page_num={page_num}&with_product_attributes=true&qs=false'
	# url = f'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=151002447951&facets_required=1&products_per_page=21&page_num={page_num}&with_product_attributes=true&qs=false'
	url = f'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=151002447951&facets_required=1&products_per_page=21&page_num={page_num}&with_product_attributes=true&qs=false'
	html = get_zenrows_html(url)
	data = json.loads(html)

	for product in data['items']:
		source_url = 'https://www.dtlr.com' + product['u']
		for v in product['vra']:
			for i in v[1]:
				if i[0] == 'Barcode':
					upc = i[1][0]
				if i[0] == 'Price':
					price = i[1][0].split(':')[1]
				if i[0] == 'Size':
					variant = i[1][0]

			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, variant, source_url])
	with counter_lock:
		counter += 1
		print(f"Getting pages {counter} / {total_pages}", end='\r')


if __name__ == "__main__":
	# url = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=151002447951&facets_required=1&products_per_page=21&page_num=1&with_product_attributes=true&spv=%7B%228542653317354%22:1753871179%7D&st=undefined&qs=false'
	# url = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=442884227306&facets_required=1&products_per_page=21&page_num=1&with_product_attributes=true&qs=false'
	# url = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=151002447951&facets_required=1&products_per_page=21&page_num=1&with_product_attributes=true&qs=false'
	url = 'https://api.fastsimon.com/categories_navigation?request_source=v-next&src=v-next&UUID=1457daa8-607c-45d8-bc5a-8731f937212c&uuid=1457daa8-607c-45d8-bc5a-8731f937212c&store_id=9544204367&api_type=json&category_id=151002447951&facets_required=1&products_per_page=21&page_num=1&with_product_attributes=true&qs=false'
	html = get_zenrows_html(url)
	data = json.loads(html)
	total_pages = math.ceil(int(data['total_results']) / 21)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, i, total_pages) for i in range(total_pages)]
		# Optional: Wait for all threads to finish
		concurrent.futures.wait(futures)

	print("\n\nDone")