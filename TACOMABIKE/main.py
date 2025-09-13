import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
import time
from playwright.sync_api import sync_playwright
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

write_filename = "final_tacoma_bike_" + date_now + ".csv"
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

def get_zenrows_html(target_url, waitt):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait_for': waitt,
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	global urls
	url = 'https://toolup.com/collections/tacoma-bike'
	url = f'{url}?page={page}'
	html = get_zenrows_html(url, 'ul.gap-x-theme')
	soup = BeautifulSoup(html, 'html.parser')
	
	products = soup.find('ul', class_='gap-x-theme').find_all('li', class_='js-pagination-result')
	for product in products:
		with counter_lock:
			urls.append('https://toolup.com'+product.find('a').get('href'))   

def get_product_info(link):
	html = get_zenrows_html(link+'.json', 'body')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = variant['price']
		title = variant['title']

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, link])

if __name__ == "__main__":
	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	start_url = "https://tacomabike.com/collections/sale-items?sort_by=discount&tab=products"
	page.goto(start_url, wait_until="load")
	time.sleep(5)


	next_btn = page.locator("a.snize-pagination-load-more")
	next_btn.scroll_into_view_if_needed()
	time.sleep(1)

	try:
		while True:
			next_btn = page.locator("a.snize-pagination-load-more")
			if next_btn.count() == 0:
				break

			next_btn.scroll_into_view_if_needed()
			time.sleep(1)
			try:
				next_btn.click(timeout=10000)
				time.sleep(2)
			except Exception:
				break

			try:
				page.wait_for_load_state("networkidle", timeout=1000)
			except Exception:
				time.sleep(2)


		soup = BeautifulSoup(page.content(), "html.parser")
		for prod in soup.find('ul', class_='snize-search-results-content').find_all("li", class_='snize-product-in-stock'):
			url = 'https://tacomabike.com' + prod.find('a').get('href')
			if url not in urls:
				urls.append(url)

	finally:
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