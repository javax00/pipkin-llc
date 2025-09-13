from tabnanny import check
import requests
import time
import os
import csv
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import json
import concurrent.futures
import threading
from concurrent.futures import as_completed
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

write_filename = "final_vitacost_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Promotion', 'Source URL']
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
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait_for': 'ul.productWrapper'
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

# Helper to scrape a single page
def scrape_page(page):
	# url = f'https://www.vitacost.com/productsearch.aspx?rid=1000102.01&pg={page}'
	# url = f'https://www.vitacost.com/select-non-gmo?pg={page}'
	url = f'https://www.vitacost.com/clearance-items?pg={page}'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")

	for product in soup.find('ul', class_='productWrapper').find_all('li', class_='product-block'):
		source_url = 'https://www.vitacost.com'+product.find('a', class_='ellipsis60').get('href')
		promos = []
		if product.find('ul', class_='main-block'):
			for promo in product.find_all('li', class_='srp-promo'):
				promos.append('['+promo.text.strip()+']')
			promotion = ', '.join(promos)
		data = json.loads(product.find('a', class_='ellipsis60').get('data-iteminfo'))

		upc = data['sku']
		price = float(data['unitPrice'])*.82

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, promotion, source_url])

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = int(get_pages)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(scrape_page, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\n\nDone.')
