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

write_filename = "final_rununited_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Source']
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

def get_product_links(page):
	url = f'https://searchserverapi1.com/getresults?api_key=1R3G2s3d0j&q=&sortBy=created&sortOrder=desc&startIndex={page}&maxResults=20&items=true&pages=true&categories=true&suggestions=true&queryCorrection=true&suggestionsMaxResults=3&pageStartIndex=0&pagesMaxResults=20&categoryStartIndex=0&categoriesMaxResults=20&facets=true&facetsShowUnavailableOptions=false&recentlyViewedProducts=&recentlyAddedToCartProducts=&recentlyPurchasedProducts=&ResultsTitleStrings=2&ResultsDescriptionStrings=2&tab=products&action=moreResults&page=2&category=https%3A%2F%2Frununited.com%2Fsale%2F&displaySubcatProducts=always&CustomerGroupId=2&timeZoneName=Asia%2FManila&output=jsonp&callback=jQuery371007584844357549236_1756798806975&_=1756798806977'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	data_json = json.loads(soup.text.replace('jQuery371007584844357549236_1756798806975(', '').replace(');', ''))
	for item in data_json['items']:
		for i in item['bigcommerce_variants']:
			upc = i['upc']
			if len(upc) == 12:
				upc = '0'+upc
			price = i['price']
			source_url = i['link']

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, source_url])


if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/20)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*20) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\nDone')