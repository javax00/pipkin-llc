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

write_filename = "final_tacticalgear_" + date_now + ".csv"
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

infos = []

def get_product_links(page):
	url = "https://m5e232tzvb-1.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.24.0)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.77.1)%3B%20JS%20Helper%20(3.23.1)&x-algolia-api-key=41141782d5fe54a59d73048c963115f5&x-algolia-application-id=M5E232TZVB"

	payload = "{\"requests\":[{\"indexName\":\"prod_TG\",\"params\":\"attributesToRetrieve=%5B%22style%22%2C%22title%22%2C%22brand%22%2C%22url%22%2C%22image_path_style_lvl%22%2C%22image_path_sku_lvl%22%2C%22color_swatch_style_lvl%22%2C%22ratings_in_average%22%2C%22ratings_total_count%22%2C%22web_keywords.Today's%20Deals%22%2C%22web_attributes.Features%22%2C%22price.price_base%22%2C%22price.price_sale%22%2C%22price_map%22%2C%22private_label%22%2C%22purchases_style_lvl%22%2C%22views%22%2C%22add_to_cart%22%2C%22ratings_total_count%22%2C%22ratings_in_average%22%2C%22stock_status_lex%22%2C%22clearance%22%2C%22sale_item%22%2C%22new_arrival%22%2C%22shipsfree_item%22%2C%22productId%22%2C%22productGroupId%22%2C%22categoryPageId%22%2C%22productQuantityOnHand%22%5D&clickAnalytics=true&distinct=true&facets=%5B%22brand%22%2C%22categoryPageId%22%2C%22customizable_item%22%2C%22private_label%22%2C%22shipsfree_item%22%2C%22web_attributes.Price%20Range%22%2C%22web_attributes.Shoe%20Size%22%2C%22web_attributes.Shoe%20Width%22%2C%22web_keywords.Activity%22%2C%22web_keywords.Color%22%2C%22web_keywords.Compliance%22%2C%22web_keywords.Fabric%22%2C%22web_keywords.Features%22%2C%22web_keywords.Gender%22%2C%22web_keywords.Height%22%2C%22web_keywords.Insulation%22%2C%22web_keywords.Material%22%2C%22web_keywords.OCP%22%2C%22web_keywords.Service%22%2C%22web_keywords.Size%22%2C%22web_keywords.Today's%20Deals%22%2C%22web_keywords.Toe%20Type%22%2C%22web_keywords.Weight%22%5D&filters=(categoryPageId%3A%22Footwear%20%3E%20Boots%20%3E%20Military%20Boots%22)%20AND%20keyword_urls%3A%22military-boots%22%20AND%20clearance%3Afalse&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=24&maxValuesPerFacet=200&page="+str(page)+"&query=\"}]}"
	headers = {
		'Content-Type': 'text/plain'
	}

	response = requests.post(url, headers=headers, data=payload)

	for item in response.json()['results'][0]['hits']:
		price = item['price']['price_base'][0]['low_price']
		with counter_lock:
			infos.append([item['productGroupId'], price])

def get_product_info(pid, price):
	url = "https://api.bazaarvoice.com/data/products.json?passkey=caQyjkJs6TlI9s1lLBPy1NgjjP7VUaarMkrr8R5xwlyfs&locale=en_US&allowMissing=true&apiVersion=5.4&filter=id:"+str(pid)

	headers = {
		'sec-ch-ua-platform': '"Windows"',
		'Referer': 'https://tacticalgear.com/',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0'
	}

	response = requests.get(url, headers=headers)

	finals = []
	for i in response.json()['Results']:
		source_url = i['ProductPageUrl']
		if i['UPCs']:
			for upc in i['UPCs']:
				finals.append(['0'+upc, price, source_url])

		if i['EANs']:
			for upc in i['EANs']:
				finals.append([upc, price, source_url])
	
	for final in finals:
		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow(final)

if __name__ == "__main__":
	get_products = input('Enter total products: ')

	total_pages = math.ceil(int(get_products)/24)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(infos)} product links\n')

	# infos = infos[:2]

	counter = 0
	counter_lock = threading.Lock()

	total = len(infos)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, pid, price) for pid, price in infos]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')