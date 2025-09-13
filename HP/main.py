import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
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

write_filename = "final_hp_" + date_now + ".csv"
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

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us'
	}
	r = requests.get(zenrows_api, params=params, timeout=60)
	return r.text

def get_product_info(url):
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	div = soup.find('div', id='data')
	comment = div.find(string=lambda text: isinstance(text, Comment))
	data_json = json.loads(comment.strip())

	datas = data_json['slugInfo']['components']
	upc = datas['productInitial']['upc']
	price = datas['productInitialPrice']['salePrice']

	with open(write_csv, 'a', newline='', encoding='utf-8') as f:
		writer = csv.writer(f)
		writer.writerow([upc, price, url])

if __name__ == "__main__":
	url = 'https://www.hp.com/us-en/shop/slp/weekly-deals'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	total_products = soup.find('span', class_='Ph-Pi_gf').text
	print(f'Total products {total_products} found')

	div = soup.find('div', id='data')
	comment = div.find(string=lambda text: isinstance(text, Comment))
	data_json = json.loads(comment.strip())

	urls = []
	for product in data_json['productData']['productInfo']['productList']['slp/weekly-deals:productTab:top-deals']['products']:
		try:
			urls.append(product["linkUrl"])
		except:
			continue

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product datas {counter} / {total}", end='\r')

	print('Done')