import dis
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
import re
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

write_filename = "macys_final_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variation', 'Promo', 'Source Link']
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

read_filename = "macys_product_urls_" + date_now + ".csv"
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
		'wait': '5000'
	}
	response = requests.get(zenrows_api, params=params, timeout=90)
	return response.text

def scrape_and_save(product):
	global counter

	html = get_zenrows_html(product[0])
	soup = BeautifulSoup(html, "html.parser")
	script = soup.find('script', id='productMktData')

	discount = 0
	if soup.find('span', class_='price-red'):
		discount = soup.find_all('span', class_='price-red')[-1].text.split(' ')[1]
		discount = int(re.findall(r'\d+\.?\d*', discount)[0])

	promo = ''
	if soup.find('span', class_='withOffer'):
		promo = soup.find('span', class_='withOffer').text.replace(' with ', '')

	json_data = script.get_text(strip=True)
	if 'SKU' not in json_data:
		return

	json_data = json.loads(json_data)
	for sku in json_data['offers']:
		upc = sku['SKU'].replace('USA', '')
		variation = sku['itemOffered']['color']
		source_link = product[0]

		if discount != 0:
			price = float(sku['price'])
			price = price - (price * (discount / 100))
		else:
			price = sku['price']

		with counter_lock:  # Use your thread lock for writing
			with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
				writer = csv.writer(file)
				writer.writerow([upc, price, variation, promo, source_link])

	with counter_lock:
		print(f"Scraping UPCs {counter} / {len(products)}")
		counter+=1

if __name__ == "__main__":
	with ThreadPoolExecutor(max_workers=80) as executor:
		executor.map(scrape_and_save, products)
	
	print('Done')