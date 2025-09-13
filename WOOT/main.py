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

write_filename = "final_woot_" + date_now + ".csv"
write_headers = ['ASIN', 'Price', 'Source Link']
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
	global urls

	graphql_query = """
		{
		searchOffers(Filter:
		{
			Categories: ["home", "tech", "pc", "tools", "sport", "grocery"],
			IsSoldOut:
			{
				exclude: true
			}
		}, Sort: BestSelling, Limit: 12, Skip: """+str(page)+""")
		{
			Offers
			{
				Slug
			}
		}
	}"""

	target_url = "https://d24qg5zsx8xdc4.cloudfront.net/graphql?query=" + urllib.parse.quote(graphql_query, safe="")

	# params = {
	# 	"apikey": ZENROWS_API_KEY,
	# 	"url": target_url,
	# 	"premium_proxy": "true",
	# 	"proxy_country": "us",
	# 	"js_render": "false",
	# 	"custom_headers": "true",
	# }

	headers = {
		"x-api-key": "da2-hk2jpo7aljfvxollvmieghuqlu",
		"Accept": "application/json",
	}

	r = requests.get(target_url, headers=headers, timeout=90)
	for item in r.json()['data']['searchOffers']['Offers']:
		with counter_lock:
			urls.append('https://sellout.woot.com/offers/'+item['Slug'])

def get_product_info(link):
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	for script in soup.find_all("script"):
		if 'var offerItems = ' in script.get_text():
			text = script.get_text()
			m = re.search(r'(?:var|let|const)\s+offerItems\s*=\s*(\[[\s\S]*?\]);', text)
			if m:
				offer_items = json.loads(m.group(1))
				asin = offer_items[0]['Asin']
				price = offer_items[0]['SalePrice']
				
				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([asin, price, link])

				break

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = int(get_pages)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*12) for i in range(total_pages)]
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