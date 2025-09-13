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

write_filename = "final_outdoorresearch_" + date_now + ".csv"
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

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	sale_price = soup.find("span", class_="sales").find("span").get('content')
	
	if str(sale_price) == "null":
		return

	for script in soup.find_all("script"):
		text = script.get_text()
		if "catalogProductString" in text:
			upcs = get_catalog_clean_json_and_obj(text)
			for upc in upcs['upcs']:
				with counter_lock:
					with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
						writer = csv.writer(file)
						writer.writerow([upc, sale_price, link])
			break

def get_catalog_clean_json_and_obj(html_text):
	try:
		m = re.search(r'window\.bvData\.catalogProductString\s*=\s*"((?:[^"\\]|\\.)*)"', html_text, re.DOTALL)
		if not m:
			return None
		clean_json_str = json.loads(m.group(1)[1:-1].replace('\\', ''))
		return clean_json_str
	except Exception as e:
		print(str(e))
		return None

if __name__ == "__main__":
	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	base_url = "https://www.harmanaudio.com"
	start_url = "https://www.harmanaudio.com/summer-sale/"
	page.goto(start_url, wait_until="load")
	time.sleep(5)

	next_btn = page.locator("button.more").first
	next_btn.scroll_into_view_if_needed()

	try:
		while True:
			next_btn = page.locator("button.more").first
			if next_btn.count() == 0:
				break

			next_btn.scroll_into_view_if_needed()
			try:
				next_btn.click(timeout=1000)
				time.sleep(5)
			except Exception:
				break

			try:
				page.wait_for_load_state("networkidle", timeout=1000)
			except Exception:
				time.sleep(2)

		soup = BeautifulSoup(page.content(), "html.parser")
		grid = soup.select_one("div#product-grid-plp")
		for a in grid.select("div.tile a#image-url[href]"):
			url = base_url + a["href"]
			if url not in urls:
				urls.append(base_url + a["href"])

	finally:
		context.close()
		browser.close()
		p.stop()

	print(f'\nFound {len(urls)} product links\n')

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')