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

counter = 1                     # <-- Shared counter for all threads
counter_lock = threading.Lock() # <-- Lock for thread safety

############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_kipling_" + date_now + ".csv"
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

read_filename = "kipling_product_urls_" + date_now + ".csv"
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
		response = requests.get(url, timeout=60)
		response.raise_for_status()
		return response.text
	except requests.exceptions.RequestException as e:
		print(f"Error fetching the page: {e}")
		return None

def scrape_product(product):
	global counter
	while True:
		try:
			html = get_zenrows_html(product[0])
			soup = BeautifulSoup(html, "html.parser")
			wrappers = soup.find_all('div', class_='main-product-standard-option-color__list-wrapper')
			break
		except Exception as e:
			print(f"Retrying {counter}...")
			time.sleep(5)
			continue

	for wrapper in wrappers:
		items = wrapper.find_all('div', class_='main-product-standard-option-color__item')
		for item in items:
			json_data = item.find('input').get('data-product')
			json_data = json.loads(json_data)

			get_price = json_data['variants'][0]['price']
			get_price = float(get_price) / 100
			price = f"{get_price:.2f}"

			upc = json_data['variants'][0]['barcode']
			variation = json_data['variants'][0]['title']
			source_link = 'https://us.kipling.com/products/' + json_data['handle']

			with threading.Lock():
				with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
					writer = csv.writer(file)
					writer.writerow([upc, price, variation, source_link])

	# Thread-safe counter increment
	with counter_lock:
		print(f"Scraping UPCs {counter} / {len(products)}")
		counter += 1

if __name__ == "__main__":
	with ThreadPoolExecutor(max_workers=10) as executor:
		executor.map(scrape_product, products)

	print('Done')