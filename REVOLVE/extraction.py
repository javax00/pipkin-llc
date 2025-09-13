import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
from datetime import datetime

counter = 0
counter_lock = threading.Lock()

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_revolve_" + date_now + ".csv"
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

read_filename = "product_urls_revolve_" + date_now + ".csv"
############################# CSV READ ##################################
script_dir = os.path.dirname(os.path.abspath(__file__))     			#
read_csv = os.path.join(script_dir, read_filename) 						#
																		#
products = []															#
with open(read_csv, 'r', encoding='utf-8') as f:						#
	reader = csv.reader(f)												#
	header = next(reader)												#
	for row in reader:													#
		products.append(row)											#
############################# CSV READ ##################################

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_single_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
		'wait_for': 'div.pdp__description-wrap'
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_upc(keyword):
	target_url = f"https://api.upcitemdb.com/prod/trial/search?s={keyword}"
	result = get_zenrows_html(target_url)

	if 'RESP002' not in result:
		data = json.loads(result)
		upcs = []
		for item in data["items"]:
			upcs.append(item['ean'])
		return upcs
	return []

def get_manuf_num(url):
	html = get_single_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	brand = soup.find('h1').text.strip().replace('\n', ' ').replace('                      ', ' ')
	price = soup.find('span', id='markdownPrice').text.split('$')[1]
	try:
		color = soup.find('span', class_='selectedColor').text.strip()
	except:
		color = ''

	upcs = get_upc(brand)
	if upcs != []:
		for upc in upcs:
			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, color, url])

if __name__ == "__main__":
	total = len(products)
	print('Total Products: ', total)

	# get_manuf_num('https://www.revolve.com/project-lip-plump-jelly-in-booty-call/dp/PROL-WU28/?d=Womens&page=15&lc=48&itrownum=14&itcurrpage=15&itview=05')
	# products = products[:10]

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_manuf_num, product[0]) for product in products]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r', flush=True)
	
	print('\n\nDone.')