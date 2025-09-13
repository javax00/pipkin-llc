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

write_filename = "final_adidas_" + date_now + ".csv"
write_headers = ['Keyword', 'Price', 'Promo', 'Source Link']
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

dups = []

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

def get_product_keyword(page):
	global dups
	reps = 1
	while True:
		try:
			# url = f'https://www.adidas.com/plp-app/_next/data/pUxgrdUpuWeWbftJ51G-4/us/men-shop.json?start={page}&path=us&taxonomy=men-shop'
			url = f'https://www.adidas.com/plp-app/_next/data/FaHwjlOB4kkp2Z91zX5jP/us/sale.json?start={page}&path=us&taxonomy=sale'
			html = get_zenrows_html(url)
			data_json = json.loads(html)

			for item in data_json['pageProps']['products']:
				price = item['priceData']['salePrice']
				promo = ''
				try:
					promo = item['badge']['text']
				except:
					pass
				source_url = 'https://www.adidas.com' + '/'.join(item['url'].split('/')[:-1]) + '/'
				for var in item['colourVariations']:
					if var not in dups:
						dups.append(var)
						with counter_lock:
							with open(write_csv, 'a', newline='', encoding='utf-8') as f:
								writer = csv.writer(f)
								writer.writerow([var, price, promo, source_url+var+'.html'])	
			break
		except:
			if reps == 3:
				return
			reps += 1

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = math.ceil(int(get_pages)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_keyword, i*48) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\n\nDone.')
