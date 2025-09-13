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
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_cotopaxi_" + date_now + ".csv"
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
	links = [
		'https://www.cotopaxi.com/collections/sale',
		'https://www.cotopaxi.com/collections/new-to-sale',
		'https://www.cotopaxi.com/collections/packs-sale',
		'https://www.cotopaxi.com/collections/womens-sale',
		'https://www.cotopaxi.com/collections/mens-sale',
		'https://www.cotopaxi.com/collections/accessories-sale',
		'https://www.cotopaxi.com/collections/kids-sale',
		'https://www.cotopaxi.com/collections/extra-10-sale'
	]
	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	# stealth_sync(page)

	for link in links:
		page.goto(link, wait_until="load")
		input('Enter if done scrolling: ')

		soup = BeautifulSoup(page.content(), "html.parser")
		for item in soup.find('div', class_='product-grid-row').find_all('div', class_='ctpx-product-item'):
			url = 'https://cotopaxi.com'+item.find('a')['href'].split('?')[0]
			if url not in urls:
				urls.append(url)

	context.close()
	browser.close()
	p.stop()

	print(f'Found {len(urls)} product links\n')


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