import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))

counter = 1                     # <-- Shared counter for all threads
counter_lock = threading.Lock() # <-- Lock for thread safety

############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "macys_product_urls_" + date_now + ".csv"
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

# read_filename = "ck_product_urls.csv"
# ############################# CSV READ ##################################
# script_dir = os.path.dirname(os.path.abspath(__file__))     			#
# read_csv = os.path.join(script_dir, read_filename) 						#
# 																		#
# products = []															#
# with open(read_csv, 'r', encoding='utf-8') as f:						#
# 	reader = csv.reader(f)												#
# 	header = next(reader)												#
# 	for row in reader:													#
# 		products.append(row)											#
# ############################# CSV READ ##################################

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
		'wait': '5000'
	}
	r = requests.get(zenrows_api, params=params, timeout=60)
	return r.text

def scrape_and_save(i, total_page):
	global counter
	# url = f"https://www.macys.com/shop/sale/clearance-closeout/Pageindex/{i}?id=54698"
	# url = f"https://www.macys.com/shop/sale/black-friday-deals/Pageindex/{i}?id=62204"
	url = f'https://www.macys.com/shop/sale/Business_category,Pageindex/Activewear%7CWomen%27s%20Clothing%7CVitamins%20%26%20Supplements%7CBeauty%7CKids%20%26%20Baby,{i}?id=3536'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")

	products = soup.find_all('li', class_='sortablegrid-product')
	for product in products:
		if 'sortable-grid-monetization-items' not in product.get('class'):
			product_url = "https://www.macys.com" + product.find_all('a')[0].get('href').split('&swatch')[0]
			with counter_lock:
				with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
					writer = csv.writer(file)
					writer.writerow([product_url])
			print(f"Page {counter} / {total_page}")
			counter+=1

if __name__ == "__main__":
	# url = 'https://www.macys.com/shop/sale/clearance-closeout?id=54698'
	# url = 'https://www.macys.com/shop/sale/black-friday-deals?id=62204'
	url = 'https://www.macys.com/shop/sale/Business_category/Activewear%7CWomen%27s%20Clothing%7CVitamins%20%26%20Supplements%7CBeauty%7CKids%20%26%20Baby?id=3536'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")
	total_page = soup.find('div', class_='numeric-pagination-wrapper').text.strip().split('.')[-1]
	print('Total pages: ' + total_page)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(scrape_and_save, i, total_page) for i in range(1, int(total_page)+1)]
		for future in as_completed(futures):
			pass  # Or add error logging if you want

	print('Done')
