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

write_filename = "final_walkingpad_" + date_now + ".csv"
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

urls = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
	}
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = variant['price']
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	urls = [
		'https://www.walkingpad.com/products/walkingpad-x25-treadmill?variant=45585831919873',
		'https://www.walkingpad.com/products/walkingpad-x21-foldable-treadmill',
		'https://www.walkingpad.com/products/walkingpad-c1-walking-machine',
		'https://www.walkingpad.com/products/walkingpad-c2-foldable-walking-machine',
		'https://www.walkingpad.com/products/walkingpad-mc11-workout-treadmill-for-running',
		'https://www.walkingpad.com/products/walkingpad-a1-pro-foldable-treadmill',
		'https://www.walkingpad.com/products/walkingpad-r2-foldable-treadmill',
		'https://www.walkingpad.com/products/walkingpad-z1-under-desk-treadmill',
		'https://www.walkingpad.com/products/w1b-foldable-exercise-bike',
		'https://www.walkingpad.com/products/wm10-trifold-water-rowing-machine',
		'https://www.walkingpad.com/products/walkingpad-r1-pro-2in1-foldable-treadmill',
		'https://www.walkingpad.com/products/walkingpad-z1-white-folding-treadmill',
		'https://www.walkingpad.com/products/walkingpad-office-chair',
		'https://www.walkingpad.com/products/walkingpad-r2-hybrid-with-handle',
	]

	print(f'\nFound {len(urls)} product links\n')
	print(urls[0])

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')