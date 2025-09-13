import requests
import json
import os
import csv
import re
import math
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import concurrent.futures
import threading
import time
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")
zenrows_api = 'https://api.zenrows.com/v1/'
############################## ZENROWS ##################################

write_filename = "puma_product_urls_" + date_now + ".csv"
write_headers = ['URLs']
############################# CSV WRITE #################################
script_dir = os.path.dirname(os.path.abspath(__file__))
write_csv = os.path.join(script_dir, write_filename)
if os.path.exists(write_csv):
	os.remove(write_csv)
	print(f"Deleted existing file: {write_csv}\nStarting now...\n")

with open(write_csv, 'w', newline='', encoding='utf-8') as f:
	writer = csv.writer(f)
	writer.writerow(write_headers)
############################# CSV WRITE #################################

check_url = []

csv_lock = threading.Lock()
counter = 0

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

def get_urls_post(page_no, bearer_token, total_page):
	target_url = "https://us.puma.com/api/graphql"

	params = {
		"apikey": ZENROWS_API_KEY,
		"url": target_url,
		"premium_proxy": "true",
		"proxy_country": "us",
		'custom_headers': 'true',
	}

	headers = {
		"authorization": f"Bearer {bearer_token}",
		"content-type": "application/json",
		"accept": "application/graphql-response+json, application/graphql+json, application/json",
		"referer": "https://us.puma.com/us/en/sale/all-sale",
		"locale": "en-US",
	}

	payload = {
		"operationName": "CategoryPLP",
		"query": """
		query CategoryPLP($url: String!, $filters: [FilterInputOption!]!, $offset: Int!, $limit: Int!) {
		categoryByUrl(url: $url) {
			products(input: {filters: $filters, offset: $offset, limit: $limit}) {
			nodes {
				masterId
				variantProduct {
				preview
				}
			}
			}
		}
		}
		""",
		"variables": {
			"url": "/sale/all-sale",
			"filters": [],
			"offset": page_no * 24,
			"limit": 24,
			"locale": "en-US"
		}
	}

	# response = requests.post(zenrows_api, params=params, headers=headers, json=payload, timeout=90)
	response = requests.post(target_url, headers=headers, json=payload, timeout=90)
	data = response.json()

	for prod in data['data']['categoryByUrl']['products']['nodes']:
		url = 'https://us.puma.com/us/en/pd/'+prod['variantProduct']['preview'].split('/')[-1]+'/'+prod['masterId']
		url = url.replace('"', '')
		if url not in check_url:
			check_url.append(url)
			with csv_lock:
				with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
					writer = csv.writer(file)
					writer.writerow([url])

if __name__ == "__main__":
	print('How to get Bearer Token')
	print('Go to: https://us.puma.com/us/en')
	print('Inspect element or Press F12')
	print('Go to Network tab and click Reload')
	print('Search for "graphql"')
	print('Find Authorization in headers and copy the value without "Bearer"')
	bearer_token = input('ENTER Bearer Token: ')

	# url = 'https://us.puma.com/us/en/puma/shop-all-promotions'
	# url = 'https://us.puma.com/us/en/sale/new-to-sale'
	url = 'https://us.puma.com/us/en/sale/all-sale'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")
	total_page = soup.find('span', {'data-test-id': 'product-list-total-count'}).text.strip()
	total_page = str(math.ceil(int(re.findall(r"\d+", total_page)[0]) / 24))
	print(f'Found {total_page} pages')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_urls_post, i, bearer_token, total_page) for i in range(0, int(total_page))]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total_page}", end='\r')

	print("\nDone!")
