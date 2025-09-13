import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from pathlib import Path
import re
import json
import csv
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
import threading
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")

promo = 'STORAGE15'
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'final_acmetools_'+date_now+'_'+promo+'.csv')
if os.path.exists(csv_file):
    os.remove(csv_file)
    print(f"Deleted existing file: {csv_file}\nStarting now...\n")

# CSV header
header = ['UPC', 'Price', 'Promo', 'Link']
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)

def get_zenrows_html(target_url):
	zenrows_url = "https://api.zenrows.com/v1/"
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
		'wait': '5000'
	}
	r = requests.get(zenrows_url, params=params, timeout=60)
	return r.text

def get_total_products(page_url):
	html = get_zenrows_html(page_url)
	soup = BeautifulSoup(html, "html.parser")

	total_result = soup.find('span', class_='search-result-count').text.strip().replace(',', '')
	total_result = int(re.findall(r"\d+", total_result)[0])
	print(total_result)
	return total_result

def get_product_info(page_url, i):
	retry = 1
	while True:
		try:
			page_url = f"{page_url}&start={i}&sz=96"
			html = get_zenrows_html(page_url)
			soup = BeautifulSoup(html, "html.parser")

			json_data = soup.find('script', id='product-ldjson').get_text()
			json_data = json.loads(json_data)

			items = json_data['itemListElement']
			for item in items:
				upc = str(item['item']['url']).split('/')[-1].split('.')[0]
				if upc.isdigit():
					price = float(item['item']['offers']['price'])*.85
					source_url = item['item']['url']

					with counter_lock:
						with open(csv_file, 'a', newline='', encoding='utf-8') as f:
							writer = csv.writer(f)
							writer.writerow([upc, price, promo, source_url])
			break
		except Exception as e:
			if retry == 3:
				break
			retry += 1
			time.sleep(5)

if __name__ == "__main__":
	# url = "https://www.acmetools.com/all/?pmid=25a604_klein_25off"
	# url = "https://www.acmetools.com/all/?pmid=25a938_dewalt_tier"
	url = 'https://www.acmetools.com/all/?pmid=25a695_dewalt_15off'
	# url = 'https://www.acmetools.com/all/?pmid=25a907_gearwrench_crescent_15off'
	# url = 'https://www.acmetools.com/all/?pmid=25a509_diablo_12off'

	total_result = get_total_products(url)
	total_pages = math.ceil(total_result/96)
	print(f"Total pages: {total_pages}")

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
		futures = [executor.submit(get_product_info, url, i) for i in range(0, total_result, 96)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\n\nDone.')



	
