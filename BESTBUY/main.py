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

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "product_urls_bestbuy_" + date_now + ".csv"
write_headers = ['URLs']
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

def get_zenrows_html(target_url, element, value):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
		'wait_for': f'{element}{value}'
	}
	r = requests.get(zenrows_api, params=params, timeout=60)
	return r.text

def get_product_urls(page_num, url):
	url = f'{url}?cp={page_num}'
	html = get_zenrows_html(url, 'ol', '.sku-item-list')
	soup = BeautifulSoup(html, 'html.parser')

	for product in soup.find('ol', class_='sku-item-list').find_all('li', class_='sku-item'):
		product_url = 'https://www.bestbuy.com' + product.find('a', class_='image-link')['href']

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([product_url])

if __name__ == "__main__":
	# url = 'https://www.bestbuy.com/site/all-health-wellness-fitness-on-sale/personal-care-beauty-on-sale/pcmcat1721143245916.c'
	# url = 'https://www.bestbuy.com/site/all-electronics-on-sale/all-health-wellness-fitness-on-sale/pcmcat1690897564372.c'
	url = 'https://www.bestbuy.com/site/top-deals/all-electronics-on-sale/pcmcat1674241939957.c'
	html = get_zenrows_html(url, 'span', '.item-count')
	soup = BeautifulSoup(html, 'html.parser')

	get_total = soup.find('span', class_='item-count').text
	total_pages = math.ceil(int(get_total.split(' ')[0])/18)
	print(f'Found {total_pages} pages')

	if total_pages >= 100:
		total_pages = 100
		print(f'Limited to {total_pages} pages...\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_urls, i, url) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Extracting datas {counter} / {total_pages}", end='\r')

	print("\n\nDone")

	

	