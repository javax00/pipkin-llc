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
import math
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

write_filename = "kipling_product_urls_" + date_now + ".csv"
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
		'proxy_country': 'us'
	}
	# r = requests.get(zenrows_api, params=params, timeout=60)
	r = requests.get(target_url, timeout=60)
	return r.text

if __name__ == "__main__":
	# url = 'https://us.kipling.com/collections/back-to-school-view-all'
	# url = 'https://us.kipling.com/collections/flash-sale'
	url = 'https://us.kipling.com/collections/kipling-outlet-viewall'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")
	total_page = soup.find('span', class_='plp_header-collection-details__count').text.strip()
	total_page = str(math.ceil(int(re.findall(r"\d+", total_page)[0]) / 24))
	
	for i in range(1, int(total_page)+1):
		print(f"Processing {i} of {total_page}")
		url = f"{url}?page={i}"
		html = get_zenrows_html(url)
		soup = BeautifulSoup(html, "html.parser")
		products = soup.find_all('div', class_='product-card__content')
		for product in products:
			product_url = "https://us.kipling.com" + product.find('a').get('href')

			with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
				writer = csv.writer(file)
				writer.writerow([product_url])