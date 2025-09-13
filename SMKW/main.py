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

write_filename = "final_smkw_" + date_now + ".csv"
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
	# url = f'https://p6tgz5.a.searchspring.io/api/search/search.json?cart=AUMT2321XWSMK%2CPDSMKW21&lastViewed=AUKS9000LWS&userId=2d0d1cc1-159c-4b86-afcf-aff2355fdd14&domain=https%3A%2F%2Fsmkw.com%2Fspecials%2F%3Fp%3D2&sessionId=07da33b1-9e9b-47cd-9738-3df273e0973a&pageLoadId=6eaae223-8df0-40d8-a414-0c92e7fb3b36&siteId=p6tgz5&page={page}&bgfilter.categories_hierarchy=Specials&redirectResponse=full&ajaxCatalog=Snap&resultsFormat=native'
	url = f'https://p6tgz5.a.searchspring.io/api/search/search.json?lastViewed=AUKS9000LWS&userId=2d0d1cc1-159c-4b86-afcf-aff2355fdd14&domain=https%3A%2F%2Fsmkw.com%2Fspecials%2F%3Fp%3D2&sessionId=75687d27-7d96-4b52-b68d-0ead56c0a5cc&pageLoadId=0b3f4131-1339-41ec-9e9e-3a3b7a57d80d&siteId=p6tgz5&page={page}&bgfilter.categories_hierarchy=Specials&redirectResponse=full&noBeacon=true&ajaxCatalog=Snap&resultsFormat=native'
	html = get_zenrows_html(url)
	data_json = json.loads(html)
	for item in data_json['results']:
		urls.append([item['uid'], 'https://smkw.com'+item['url'], item['price']])

def get_product_info(pid, link, price):
    target_url = f"https://smkw.com/remote/v1/product-attributes/{pid}"
    payload = f"action=add&product_id={pid}&qty%5B%5D=1"

    params = {
        "apikey": ZENROWS_API_KEY,
        "url": target_url,
        "premium_proxy": "true",
        "proxy_country": "us",
        "js_render": "true",       # set to false if no JS needed
        "custom_headers": "true",  # allow ZenRows to forward our headers
    }

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "x-sf-csrf-token": "20ad17b2-dfce-4d7d-82e5-e9572501ce97",
        "cookie": "cf_clearance=df5_WuIUWW2soZT3Read7z7d_Y.psBWwYeLz2lvKFwI-1755166211-1.2.1.1-6wZ76hRcC33j0HLo.XxWJVMJSOdo0EwJouXxxkFVYUIYfSRE6PeY0AzDK8whuAfGqUk.NP6I2yW.OjZRHbh9vTdSdZe.0sfnuhgoLWKLS_zHM2POsP0EOcK2c5CFbmyubiTZZOk2s6t54izv6_2WVXLd1Am0oA8P624i_CeocqnVSqsijAzdibC1FcdPII2nPrgwrVZMoZTChN25SFoOP_ugs96SQ9C9CY5aQYHRq1A; fornax_anonymousId=03cb83b9-7db1-413d-a98f-581f521b0f04; ssUserId=2d0d1cc1-159c-4b86-afcf-aff2355fdd14; _isuid=2d0d1cc1-159c-4b86-afcf-aff2355fdd14; _shg_user_id=de1702f5-8643-40b6-a420-c4d1e37a863d; tracking-preferences={%22version%22:1%2C%22destinations%22:{}%2C%22custom%22:{%22marketingAndAnalytics%22:true%2C%22advertising%22:true%2C%22functional%22:true}}; bc_consent=%7B%22allow%22%3A%5B2%2C3%2C4%5D%2C%22deny%22%3A%5B%5D%7D; _ga=GA1.1.903891958.1755166219; GSIDOxai8tu7LBl4=68c3f084-3bd2-49d3-8675-00bdb676590d; STSIDOxai8tu7LBl4=1ea2e6dc-12ec-48f7-ae85-69186335d972; ssViewedProducts=AUKS9000LWS; ltk-age-confirmed=1; SF-CSRF-TOKEN=20ad17b2-dfce-4d7d-82e5-e9572501ce97; athena_short_visit_id=37578ad7-3d1f-45f3-be24-fa474e3b7f96:1756454642; XSRF-TOKEN=0e8cd60889781e594881c585757c0eeb1ba00dd0ee30262fda2438b87b996145; SHOP_SESSION_TOKEN=3945efc9-6dc9-4963-9c91-bf7fe74cfe69; __cf_bm=iNEwulP1UCo0w.AqjfjS9iDkFM3zYtK4vbJEBbK5I00-1756454642-1.0.1.1-syKT9KTh6bn8Tu8xds8Kn3yyjGOhmGuGm9M7CWQLd8pIMcCns5ABINNvww8qAulUzpLSIdPfhfXPyJ22fJaaS7dolIaErxCrQxQfkUUvjcA; script-tag-bc-stores/9ovoti0bdi=O9H3QVXy0Y3FahJX; ssSessionId=75687d27-7d96-4b52-b68d-0ead56c0a5cc; _shg_session_id=e429c2d0-f681-4d52-9a46-b4e87fd4d08d; STORE_VISITOR=1; ltkSubscriber-AccountCreate=eyJsdGtDaGFubmVsIjoiZW1haWwiLCJsdGtUcmlnZ2VyIjoibG9hZCJ9; ltkSubscriber-NewsletterSignup=eyJsdGtDaGFubmVsIjoiZW1haWwiLCJsdGtUcmlnZ2VyIjoibG9hZCIsImx0a3NvdXJjZSI6Ik9uIn0%3D; ltk-suppression-609d5439-6621-4ddf-8be5-8abf16c460fa=1; offers-tier-Oxai8tu7LBl4=KS; _vuid=f8d51d9f-ff78-4305-98a8-985a8efb30e3; ltk-suppression-72bda948-18b5-44e7-a20e-9b61634ac325=1; lastVisitedCategory=22; Shopper-Pref=71A15061D93D65388895B7555B386C6224A827F4-1757059630905-x%7B%22cur%22%3A%22USD%22%2C%22funcConsent%22%3Atrue%7D; _ga_9LCTK9G4CL=GS2.1.s1756454646^$o2^$g1^$t1756454831^$j8^$l0^$h0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # r = requests.post("https://api.zenrows.com/v1/", params=params, headers=headers, data=payload, timeout=90)
    r = requests.post(target_url, headers=headers, data=payload, timeout=90)
    data_json = json.loads(r.text)

    upc = data_json['data']['upc']
    
    with counter_lock:
        with open(write_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([upc, price, link])

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = int(get_pages)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
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
		futures = [executor.submit(get_product_info, pid, url, price) for pid, url, price in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')