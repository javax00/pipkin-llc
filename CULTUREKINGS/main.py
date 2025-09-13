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

write_filename = "final_culturekings_" + date_now + ".csv"
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
	r = requests.get(target_url)
	return r.text

def get_product_links(page):
	url = "https://22mg8hzkho-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.12.2)%3B%20Browser%20(lite)%3B%20JS%20Helper%20(3.7.0)%3B%20react%20(17.0.1)%3B%20react-instantsearch%20(6.22.0)&x-algolia-api-key=120a2dd1a67e962183768696b750a52c&x-algolia-application-id=22MG8HZKHO"

	payload = "{\"requests\":[{\"indexName\":\"shopify_production_us_products\",\"params\":\"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&hitsPerPage=48&filters=(inStock%3Atrue%20OR%20isForcedSoldOut%3A1%20OR%20isStayInCollection%3A1)%20AND%20isOnline%3Atrue%20AND%20(NOT%20isNfs%3Atrue)%20AND%20collectionHandles%3Aall-sale&ruleContexts=%5B%22collection-all-sale%22%5D&enableRules=true&clickAnalytics=true&analyticsTags=%5B%22web%22%2C%22collection%22%2C%22all-sale%22%5D&maxValuesPerFacet=200&page="+str(page)+"&facets=%5B%22gender%22%2C%22vendor%22%2C%22sizes%22%2C%22colourPrimary%22%2C%22discountRange%22%2C%22priceRange%22%2C%22price%22%2C%22isOnSale%22%2C%22menu.categories%22%5D&tagFilters=&facetFilters=%5B%5B%22gender%3Amens%22%5D%5D\"},{\"indexName\":\"shopify_production_us_products\",\"params\":\"highlightPreTag=%3Cais-highlight-0000000000%3E&highlightPostTag=%3C%2Fais-highlight-0000000000%3E&hitsPerPage=1&filters=(inStock%3Atrue%20OR%20isForcedSoldOut%3A1%20OR%20isStayInCollection%3A1)%20AND%20isOnline%3Atrue%20AND%20(NOT%20isNfs%3Atrue)%20AND%20collectionHandles%3Aall-sale&ruleContexts=%5B%22collection-all-sale%22%5D&enableRules=true&clickAnalytics=false&analyticsTags=%5B%22web%22%2C%22collection%22%2C%22all-sale%22%5D&maxValuesPerFacet=200&page=0&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&facets=gender\"}]}"
	headers = {
		'Content-Type': 'text/plain'
	}

	response = requests.post(url, headers=headers, data=payload)

	for result in response.json()['results'][0]['hits']:
		source_url = 'https://www.culturekings.com/products/'+result['handle']
		discount = re.findall(r"\d+", result['discountRange'])[-1]
		urls.append([source_url, discount])

def get_product_info(link, discount):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = float(variant['price'])
		price = price * (1 - int(discount) / 100)
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(urls)} product links\n')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url, discount) for url, discount in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')