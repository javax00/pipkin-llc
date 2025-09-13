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

write_filename = "final_petmeds_" + date_now + ".csv"
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

def get_product_info(link):
	title = link[0]
	price = link[1]
	url = link[2]

	target_url = f"https://api.upcitemdb.com/prod/trial/search?s={title}"

	params = {
		'url': target_url,
		'apikey': ZENROWS_API_KEY,
		'premium_proxy': 'true',
		'proxy_country': 'us',
	}

	r = requests.get(zenrows_api, params=params, timeout=30)

	if 'RESP002' not in r.text:
		data = r.json()
		for item in data["items"]:
			upc = item['ean']
			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, url])

if __name__ == "__main__":
	urls = []

	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	# start_url = "https://www.1800petmeds.com/category/conditions/dog-c00017?prefn1=healthConditionTherapy&prefv1=Skin%20%2F%20Coat"
	start_url = "https://www.1800petmeds.com/hills.html?prefn1=brand&prefv1=Hill%27s%20Prescription%20Diet"
	page.goto(start_url, wait_until="load")
	time.sleep(5)

	try:
		page.wait_for_selector("div.sidebar-iframe-close", timeout=10000)
		page.click("div.sidebar-iframe-close")
	except Exception:
		pass


	next_btn = page.locator("div.show-more")
	next_btn.scroll_into_view_if_needed()
	time.sleep(1)

	try:
		while True:
			next_btn = page.locator("div.show-more")
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
		for prod in soup.find('div', class_='new-product-grid').find_all("div", class_='new-search-page-product-tile-container'):
			try:
				url = 'https://www.1800petmeds.com'+prod.find('a').get('href')

				data_json = prod.find('div', class_='product-master-tile').get('data-item-click-data-updated')
				data_json = json.loads(data_json)

				title = data_json['item_name']
				price = data_json['price']

				urls.append([title, price, url])
			except Exception:
				continue

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