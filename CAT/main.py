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
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
from datetime import datetime
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

write_filename = "final_cat_" + date_now + ".csv"
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
variants = []

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

def get_product_variants(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')
	
	variants.append(link)
	for var in soup.find("div", class_="variations-type").find("ul").find_all("li"):
		l = var.find('div', class_="linkvalue").find("a").get('href')
		if l != '#':
			variants.append(l)

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	price = soup.find("afterpay-placement").get('data-amount').split(" ")[1]
	pid = soup.find("div", id="pdpMain").get("data-pid")
	data_json = json.loads(soup.find("div", id="productDimensionsAndVariations-"+pid).get_text().strip())

	for var in data_json["variations"]:
		size = data_json["variations"][var]["size"]
		width = data_json["variations"][var]["width"]
		col_id = data_json["variations"][var]["color"]
		for color in data_json['color']['values']:
			if color['ID'] == col_id:
				color = color['displayValue']
				break

		variant = f'{color}, {width}, {size}'

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([var, price, variant, link])


if __name__ == "__main__":
	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	start_url = "https://www.catfootwear.com/US/en/construction-sale/"
	page.goto(start_url, wait_until="load")
	time.sleep(5)

	try:
		page.wait_for_selector("button#onetrust-accept-btn-handler", timeout=10000)
		page.click("button#onetrust-accept-btn-handler")
	except Exception:
		pass

	try:
		page.wait_for_function(
			"document.querySelectorAll('button.bx-button').length >= 4",
			timeout=10000
		)
		btn = page.locator("button.bx-button").nth(3)
		btn.scroll_into_view_if_needed()
		btn.click(timeout=10000)
	except Exception:
		pass

	next_btn = page.locator("button.load-more-cta").first
	next_btn.scroll_into_view_if_needed()
	time.sleep(2)

	try:
		while True:
			next_btn = page.locator("button.load-more-cta").first
			if next_btn.count() == 0:
				break

			next_btn.scroll_into_view_if_needed()
			try:
				next_btn.click(timeout=10000)
				time.sleep(5)
			except Exception:
				break

			try:
				page.wait_for_load_state("networkidle", timeout=1000)
			except Exception:
				time.sleep(2)

		soup = BeautifulSoup(page.content(), "html.parser")
		for cons in soup.select("ul#search-result-items"):
			for item in cons.select("li.grid-tile"):
				url = item.select_one("a")["href"]
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

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_variants, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product variants: {counter} / {total}", end='\r')

	print(f'\nFound {len(variants)} product variants\n')




	counter = 0
	counter_lock = threading.Lock()

	total = len(variants)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, variant) for variant in variants]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone.')