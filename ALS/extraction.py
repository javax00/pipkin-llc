import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
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

write_filename = "final_als_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variation', 'Source Link']
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

read_filename = "product_urls_als_" + date_now + ".csv"
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

def get_zenrows_html(url):
	params = {
		'url': url,
		'apikey': ZENROWS_API_KEY,
		'js_render': 'true',
		'premium_proxy': 'true',
		'proxy_country': 'us',
	}
	try:
		# response = requests.get(zenrows_api, params=params)
		response = requests.get(url, timeout=90)
		response.raise_for_status()
		return response.text
	except requests.exceptions.RequestException as e:
		print(f"Error fetching the page: {e}")
		return None

def get_info(product):
	html = get_zenrows_html(product[0])
	soup = BeautifulSoup(html, "html.parser")

	json_data = soup.find_all('script', type='application/ld+json')[1].get_text()
	json_data = json.loads(json_data)

	for variant in json_data['product']['isVariantOf']['hasVariant']:
		upc = variant['gtin']
		if not upc.isdigit():
			upc = ''
		elif len(upc) <= 10:
			upc = ''
		elif len(upc) == 11:
			upc = '00'+upc
		elif len(upc) == 12:
			upc = '0'+upc
		elif len(upc) == 14:
			upc = upc[1:]
		
		price = variant['offers']['offers'][0]['price']
		variation = variant['name']
		source_link = variant['url']

		with counter_lock:
			with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
				writer = csv.writer(file)
				writer.writerow([upc, price, variation, source_link])

if __name__ == '__main__':
	counter = [0]  # Use list for mutability
	counter_lock = threading.Lock()
	total = len(products)

	def threaded_get_info(product):
		get_info(product)
		with counter_lock:
			counter[0] += 1
			print(f"Processed {counter[0]} / {total}", end='\r')

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(threaded_get_info, product) for product in products]
		for future in as_completed(futures):
			pass  # Progress is shown inside the thread

	print("\nDone")