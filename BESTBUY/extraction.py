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

write_filename = "final_bestbuy_" + date_now + ".csv"
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

read_filename = "product_urls_bestbuy_" + date_now + ".csv"
############################# CSV READ ##################################
script_dir = os.path.dirname(os.path.abspath(__file__))     			#
read_csv = os.path.join(script_dir, read_filename) 						#
																		#
products = []															#
with open(read_csv, 'r', encoding='utf-8') as f:						#
	reader = csv.reader(f)												#
	header = next(reader)												#
	for row in reader:													#
		products.append(row)											#
############################# CSV READ ##################################

def get_zenrows_html(target_url):
	try:
		params = {
			'apikey': ZENROWS_API_KEY,
			'url': target_url,
			'premium_proxy': 'true',
			'js_render': 'true',
			'proxy_country': 'us',
			'wait': '10000'
		}
		r = requests.get(zenrows_api, params=params, timeout=120)
		return r.text
	except Exception as e:
		print(f"Error fetching {target_url}: {e}")
		return None

def get_product_info(url):
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')
	
	json_data = soup.find('script', id='product-schema').get_text()
	json_data = json.loads(json_data)

	for item in json_data['additionalProperty']:
		if item['name'] == 'UPC':
			upc = item['value']
			break
	
	price = json_data['offers'][0]['price']
	variant = ''
	try:
		variant = json_data['color']
	except:
		pass

	with counter_lock:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, variant, url])

if __name__ == "__main__":
	print(f'Scraping {len(products)} products')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, i[0]) for i in products]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Extracting datas {counter} / {len(products)}", end='\r')
			
	print("\n\nDone")