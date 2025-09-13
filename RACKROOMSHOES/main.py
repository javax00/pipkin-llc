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
import time

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_rackroomshoes_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Color', 'Source Link']
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

def get_product_info(page):
	url = "https://7cuhthvkmm-dsn.algolia.net/1/indexes/prod_rackroom_products_v1/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.24.0)%3B%20Browser"

	payload = f"{{\"query\":\"\",\"hitsPerPage\":90,\"facets\":[\"*\"],\"facetFilters\":[[\"categoryPageId:onsale\"]],\"page\":\"{page}\",\"clickAnalytics\":true}}"
	headers = {
		'Accept': '*/*',
		'content-type': 'application/x-www-form-urlencoded',
		'x-algolia-api-key': '0ace919e79993a4530700d0b32a1c429',
		'x-algolia-application-id': '7CUHTHVKMM'
	}

	response = requests.post(url, headers=headers, data=payload)

	for item in response.json()['hits']:
		upc = item['vendorUpc']
		price = item['price']
		color = item['colors'][0]
		link = 'https://www.rackroomshoes.com/p/'+str(item['sku'])

		# with counter_lock:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([upc, price, color, link])

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = math.ceil(int(get_pages)/90)
	print(f'Found {total_pages} pages\n')

	counter = 1
	for i in range(total_pages):
		if counter <= 1000:
			counter += 90
			get_product_info(i)
			print(f"Getting pages: {counter} / {get_pages}", end='\r')
		else:
			break

		time.sleep(3)

	# counter = 0
	# counter_lock = threading.Lock()

	# with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
	# 	futures = [executor.submit(get_product_info, i) for i in range(total_pages)]
	# 	for future in as_completed(futures):
	# 		with counter_lock:
	# 			counter += 1
	# 			print(f"Getting pages: {counter} / {total_pages}", end='\r')

	# print('\n\nDone')