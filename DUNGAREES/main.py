import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
from datetime import datetime
import urllib.parse
import re

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

############################## KEEPA ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
KEEPA_API_KEY = os.getenv('KEEPA_API_KEY')								#
if not KEEPA_API_KEY:													
	raise ValueError("Please set KEEPA_API_KEY in your .env file")	#
############################## KEEPA ##################################

write_filename = "final_dungarees_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Source Link']
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
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(url):
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	for item in soup.find('ul', id='products').find_all('li', class_='product'):
		name = item.find('a').text
		price = item.find('span', class_='price').text.split('$')[1].replace(' USD', '')
		url = item.find('a')['href']

		with counter_lock:
			urls.append([name, price, url])

def get_product_info(name, price, url):
	target_url = f"https://api.upcitemdb.com/prod/trial/search?s={name}"
	html = get_zenrows_html(target_url)
	data_json =	json.loads(html)

	if 'RESP002' not in html:
		for item in data_json["items"]:
			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([item['ean'], price, url])

if __name__ == "__main__":
	counter_lock = threading.Lock()
	get_product_links('https://dungarees.com/deals/summer-clearance?&view=1&sort=0&filter[c][]=0&ppg=65535&pn=1&more=&action=')

	print(f'Found {len(urls)} product links\n')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, name, price, url) for name, price, url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')
