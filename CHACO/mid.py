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

write_filename = "chaco_product_urls_final_" + date_now + ".csv"
write_headers = ['URLs']
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

read_filename = "chaco_product_urls_" + date_now + ".csv"
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

def get_each_product_links(url):
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	urls = [url.split('?')[0]]

	links = soup.find('ul', class_='customerType').find_all('li')
	for link in links:
		if link.find('label', class_='pseudolink'):
			final_url = link.find('label', class_='pseudolink').get('data-href').split('?')[0]
			urls.append(final_url)

	for url in urls:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([url])

if __name__ == "__main__":
	total = len(products)
	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_each_product_links, product[0]) for product in products]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Extracting datas {counter} / {total}", end='\r')

	print("\n\nDone")
