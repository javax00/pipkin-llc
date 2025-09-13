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
import time
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

write_filename = "final_babylisspro_" + date_now + ".csv"
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

item_nos = []

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

def get_product_info(item_no, price):
	target_url = ("https://apps.bazaarvoice.com/bfd/v1/clients/babylisspro/api-products/cv2/resources/data/batch.json?resource.q0=reviews"
	"&limit.q0=1"
	"&filter_reviews.q0=contentlocale%3Aeq%3Aen*%2Cen_US%2Cen_US"
	"&sort.q0=totalpositivefeedbackcount%3Adesc"
	"&include.q0=authors%2Creviews%2Cproducts"
	"&filter.q0=contentlocale%3Aeq%3Aen*%2Cen_US%2Cen_US"
	f"&filter.q0=productid%3Aeq%3A{item_no}"
	"&filter.q0=isratingsonly%3Aeq%3Afalse"
	"&filter.q0=issyndicated%3Aeq%3Afalse"
	"&filter.q0=totalpositivefeedbackcount%3Agte%3A3"
	"&filter.q0=rating%3Agt%3A3"
	"&resource.q1=reviews"
	"&limit.q1=1"
	"&filter_reviews.q1=contentlocale%3Aeq%3Aen*%2Cen_US%2Cen_US"
	"&sort.q1=totalpositivefeedbackcount%3Adesc"
	"&include.q1=authors%2Creviews%2Cproducts"
	"&filter.q1=contentlocale%3Aeq%3Aen*%2Cen_US%2Cen_US"
	"&filter.q1=productid%3Aeq%3ABNTSS-5PK"
	"&filter.q1=isratingsonly%3Aeq%3Afalse"
	"&filter.q1=issyndicated%3Aeq%3Afalse"
	"&filter.q1=totalpositivefeedbackcount%3Agte%3A3"
	"&filter.q1=rating%3Alte%3A3"
	"&apiversion=5.5"
	"&displaycode=10898-en_us")

	params = {
		"apikey": ZENROWS_API_KEY,
		"url": target_url,
		"custom_headers": "true",
		"premium_proxy": "true",
		"proxy_country": "us",
	}

	headers = {
		"accept": "*/*",
		"accept-language": "en-US,en;q=0.9",
		"bv-bfd-token": "10898,main_site,en_US",
		"origin": "https://babylisspro.com",
		"priority": "u=1, i",
		"referer": "https://babylisspro.com/",
		"sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		"sec-ch-ua-mobile": "?0",
		"sec-ch-ua-platform": '"Windows"',
		"sec-fetch-dest": "empty",
		"sec-fetch-mode": "cors",
		"sec-fetch-site": "cross-site",
		"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
	}

	r = requests.get('https://api.zenrows.com/v1/', params=params, headers=headers, timeout=60)
	data_json = r.json()

	data_filter = data_json['response']['BatchedResults']
	for br in data_filter:
		if data_filter[br]['Results'] != []:
			source_url = data_filter[br]['Includes']['Products'][item_no]['ProductPageUrl']
			for upc in data_filter[br]['Includes']['Products'][item_no]['UPCs']:

				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([upc, price, source_url])

if __name__ == "__main__":
	p = sync_playwright().start()
	browser = p.chromium.launch(headless=False)
	context = browser.new_context()
	page = context.new_page()

	start_url = "https://babylisspro.com/specialty-hair-tools"
	page.goto(start_url, wait_until="load")
	time.sleep(2)

	try:
		soup = BeautifulSoup(page.content(), "html.parser")
		for grid in soup.select("div.l-grid"):
			for a in grid.select("div.product-tile-wrapper"):
				price = a.find("span", class_="sales").find("span").get('content')
				item_no = a.find("div", class_="product").get("data-pid")
				item_nos.append([item_no, price])

	finally:
		context.close()
		browser.close()
		p.stop()

	print(f'\nFound {len(item_nos)} product links\n')

	counter = 0
	counter_lock = threading.Lock()

	total = len(item_nos)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, item_no, price) for item_no, price in item_nos]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')