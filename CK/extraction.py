import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import time
import json
from concurrent.futures import ThreadPoolExecutor
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

write_filename = "ck_final_" + date_now + ".csv"
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

read_filename = "ck_product_urls_" + date_now + ".csv"
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

# Thread lock for safe file writing
lock = threading.Lock()

def fetch_page(url):
	params = {
		'url': url,
		'apikey': ZENROWS_API_KEY,
		'js_render': 'true',
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'wait': '5000'
	}
	try:
		response = requests.get(zenrows_api, params=params)
		time.sleep(2)
		response.raise_for_status()
		return response.text
	except requests.exceptions.RequestException as e:
		print(f"Error fetching the page: {e}")
		return None

def fetch_and_extract(row, count, total):
	try:
		print(f"Extracting UPC: {count} / {total}")
		upc, price, variation, source_link = '', '', '', ''
		html_content = fetch_page(row[0])
		if not html_content:
			return

		soup = BeautifulSoup(html_content, 'html.parser')

		# Get price
		price_tag = soup.find('span', class_='sales')
		if price_tag:
			price = price_tag.find('span', class_='value').get('content')
		source_link = row[0]

		# Get variation data
		product_name = soup.find('span', class_='fitanalytics-view-event')
		if not product_name:
			return

		data_str = product_name.get('data-fitanalytics-view')
		data_json = json.loads(data_str)

		for dj in data_json:
			if not isinstance(data_json[dj], dict):
				continue
			size = data_json[dj].get('size')
			if not size:
				continue

			upc = dj
			variation = size

			# Lock while writing to file
			with lock:
				with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
					writer = csv.writer(file)
					writer.writerow([upc, price, variation, source_link])
	except Exception as e:
		print(f"Thread error: {e}")

if __name__ == "__main__":
	max_threads = 50
	with ThreadPoolExecutor(max_workers=max_threads) as executor:
		for i, row in enumerate(products, start=1):
			executor.submit(fetch_and_extract, row, i, len(products))

	print('Extracting completed.')
