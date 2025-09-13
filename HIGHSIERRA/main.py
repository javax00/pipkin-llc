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

write_filename = "final_highsierra_" + date_now + ".csv"
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

pids = []

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

def get_product_info(gtm):
	gtm = json.loads(gtm)
	pid = gtm['id']
	price = gtm['price']

	target_url = ("https://apps.bazaarvoice.com/api/data/products.json?resource=products"
	f"&filter=id%3Aeq%3A{pid}"
	"&filter_reviews=contentlocale%3Aeq%3Aen_US%2Cen_US"
	"&filter_questions=contentlocale%3Aeq%3Aen_US%2Cen_US"
	"&filter_answers=contentlocale%3Aeq%3Aen_US%2Cen_US"
	"&filter_reviewcomments=contentlocale%3Aeq%3Aen_US%2Cen_US"
	"&filteredstats=Reviews%2C+questions%2C+answers"
	"&stats=Reviews%2C+questions%2C+answers"
	"&passkey=caSDGTWxY7Xz0Oq88G7SwWkZMRK89BRjt6CRHKe0a2QhI"
	"&apiversion=5.5"
	"&displaycode=11918-en_us")

	params = {"apikey": ZENROWS_API_KEY, "url": target_url}

	response = requests.get(zenrows_api, params=params, timeout=60)
	json_data = response.json()
	
	source_link = json_data['Results'][0]['ProductPageUrl']
	for upc in json_data['Results'][0]['UPCs']:
		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, source_link])

if __name__ == "__main__":
	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	start_url = "https://shop.highsierra.com/sale/"
	page.goto(start_url, wait_until="load")

	input('Scroll down faster.\nEnter if done scrolling: ')

	try:
		soup = BeautifulSoup(page.content(), "html.parser")
		grid = soup.select_one("div.product-grid")
		for a in grid.select("div.product"):
			pids.append(a.get('data-gtmdata'))

	finally:
		context.close()
		browser.close()
		p.stop()

	print(f'\nFound {len(pids)} product links\n')

	counter = 0
	counter_lock = threading.Lock()

	total = len(pids)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, gtm) for gtm in pids]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')