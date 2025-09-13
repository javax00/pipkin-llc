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

write_filename = "final_frye_" + date_now + ".csv"
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

def get_product_links(page):
	url = "https://search.nosto.com/v1/graphql"

	payload = {
		"query": "query ( $abTests: [InputSearchABTest!], $accountId: String, $query: String, $segments: [String!], $rules: [String!], $products: InputSearchProducts, $keywords: InputSearchKeywords, $sessionParams: InputSearchQuery ) { search( accountId: $accountId query: $query segments: $segments rules: $rules products: $products keywords: $keywords sessionParams: $sessionParams abTests: $abTests ) { query redirect products { hits { productId url name imageUrl imageHash thumbUrl description brand variantId availability price priceText categoryIds categories customFields { key value } priceCurrencyCode datePublished listPrice unitPricingBaseMeasure unitPricingUnit unitPricingMeasure googleCategory gtin ageGroup gender condition alternateImageUrls ratingValue reviewCount inventoryLevel skus { id name price listPrice priceText url imageUrl inventoryLevel customFields { key value } availability } pid onDiscount extra { key value } saleable available tags1 tags2 tags3 } total size from facets { ... on SearchTermsFacet { id field type name data { value count selected } } ... on SearchStatsFacet { id field type name min max } } collapse fuzzy categoryId categoryPath } abTests { id activeVariation { id } } } }",
		"variables":
		{
			"accountId": "shopify-14033715254",
			"products":
			{
				"facets": ["*"],
				"categoryId": "296733540543",
				"categoryPath": "Sale",
				"size": 48,
				"from": page
			},
			"sessionParams":
			{
				"segments": ["5d8a5b683bd4f2c7cf355af7", "613aa0000000000000000002", "61c26a800000000000000002", "5b71f1500000000000000006", "61411156731b7e799bb496cf"],
				"products":
				{
					"personalizationBoost": [
					{
						"field": "affinities.categories",
						"weight": 1,
						"value": ["sale"]
					}]
				}
			},
			"abTests": []
		}
	}

	headers = {
		'accept': 'application/json, text/plain, */*',
		'accept-language': 'en-US,en;q=0.9',
		'content-type': 'text/plain',
		'origin': 'https://www.thefryecompany.com',
		'priority': 'u=1, i',
		'referer': 'https://www.thefryecompany.com/',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'cross-site',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'x-nosto-integration': 'Search Templates'
	}

	response = requests.post(url, headers=headers, json=payload)

	for item in response.json()['data']['search']['products']['hits']:
		for i in item['customFields']:
			if i['key'] == 'custom-related_styles':
				for v in i['value'].split(',')[:-1]:
					url = 'https://www.thefryecompany.com/products/'+v
					if url not in urls:
						urls.append(url)
				break

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
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*48) for i in range(total_pages)]
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
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')