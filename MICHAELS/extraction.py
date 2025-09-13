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
import xml.etree.ElementTree as ET

counter = 1                     # <-- Shared counter for all threads
counter_lock = threading.Lock() # <-- Lock for thread safety


date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_michaels_" + date_now + ".csv"
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

read_filename = "final_product_urls_michaels_" + date_now + ".csv"
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
		response = requests.get(zenrows_api, params=params)
		response.raise_for_status()
		return response.text
	except requests.exceptions.RequestException as e:
		print(f"Error fetching the page: {e}")
		return None

def get_info(product):
	html = get_zenrows_html(product[0])
	soup = BeautifulSoup(html, "xml")

	for item in soup.find_all("item"):
		if len(item.newUpcNumber.text) == 14:
			upc = '\''+item.newUpcNumber.text[2:]
		elif len(item.newUpcNumber.text) == 13:
			upc = '\''+item.newUpcNumber.text[1:]
		elif len(item.newUpcNumber.text) == 12:
			upc = '\''+item.newUpcNumber.text
		elif len(item.newUpcNumber.text) == 11:
			upc = '\'0'+item.newUpcNumber.text
		else:
			upc = ''

		variation = ''
		if item.variantAttr:
			variation = item.variantAttr.text

		price = item.itemPrice.numberPrice.text
		source_link = product[1]

		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, variation, source_link])

if __name__ == "__main__":
	total = len(products)
	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_info, product) for product in products]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Extracting datas {counter} / {total}", end='\r')

	print("\n\nDone")