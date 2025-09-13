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
import time
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

write_filename = "final_crocs_" + date_now + ".csv"
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

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
		'wait': '30000'
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def post_zenrows_html(target_url):
	# payload = "{\"requests\":[{\"indexName\":\"production_crocs_us__products__default\",\"analytics\":true,\"analyticsTags\":[\"Web\",\"Browse\"],\"attributesToRetrieve\":[\"name\",\"url\",\"image\",\"altImage\",\"gender\",\"master\",\"brand\",\"ratingPercent\",\"ratingCount\",\"pricing\",\"snipes\",\"color\",\"colorVariations\",\"colorDefaults\",\"refinementJibbitz\",\"flatCategories\",\"gender\"],\"clickAnalytics\":true,\"facets\":[\"gender\",\"jibbitable\",\"lifestyle\",\"pricing.price\",\"refinementColor\",\"refinementOccasion\",\"refinementSizes\"],\"filters\":\"categoryIDs:'outlet'\",\"highlightPostTag\":\"__/ais-highlight__\",\"highlightPreTag\":\"__ais-highlight__\",\"hitsPerPage\":748,\"maxValuesPerFacet\":100,\"page\":0,\"query\":\"\",\"userToken\":\"anonymous-6ca499fb-b69d-4d23-a1b1-801bf47c9c5e\"}]}"
	payload = '{"requests":[{"indexName":"production_crocs_us__products__default","analytics":true,"analyticsTags":["Web","Browse"],"attributesToRetrieve":["name","url","image","altImage","gender","master","brand","ratingPercent","ratingCount","pricing","snipes","color","colorVariations","colorDefaults","refinementJibbitz","flatCategories","gender"],"clickAnalytics":true,"facets":["gender","jibbitable","lifestyle","pricing.price","refinementColor","refinementOccasion","refinementSizes"],"filters":"categoryIDs:\'outlet\'","highlightPostTag":"__/ais-highlight__","highlightPreTag":"__ais-highlight__","hitsPerPage":394,"maxValuesPerFacet":100,"page":0,"query":"","userToken":"anonymous-ee1149e0-bc02-42b6-83e0-cc94a23fd34f"}]}'
	headers = {
		'Content-Type': 'text/plain'
	}
	params = {
		"apikey": ZENROWS_API_KEY,
		"url": target_url,
		"js_render": "true",
		"premium_proxy": "true",
		"wait": "30000"
	}
	r = requests.post(zenrows_api, headers=headers, params=params, data=payload, timeout=90)
	return r.text

def product_info(product_url):
	product_id = product_url.split('/')[-1].split('.')[0]

	reps = 1
	while True:
		try:
			html = get_zenrows_html(product_url)
			soup = BeautifulSoup(html, 'html.parser')

			target_script = None
			for script in soup.find_all("script", type="text/javascript"):
				if 'app.product.data.cache["'+product_id+'"].masterData' in script.get_text():
					target_script = script.get_text()
					break

			if target_script is not None:
				data = target_script.replace('app.product.data.cache["'+product_id+'"].masterData =', '').replace(';', '').strip()
				data_json = json.loads(data)

				with counter_lock:
					infos = data_json['variations']
					for info in infos:
						upc = infos[info]['UPC']
						color = infos[info]['color']
						source_url = product_url+'?cid='+color
						variant = soup.find('input', id=color).get('color-title')

						for prices in data_json['colors']:
							price = data_json['colors'][prices]['price']
							
							for gc in data_json['colors'][prices]['colors']:
								if gc == color:
									with open(write_csv, 'a', newline='', encoding='utf-8') as f:
										writer = csv.writer(f)
										writer.writerow([upc, price, variant, source_url])

				break
		except Exception as e:
			if reps == 5:
				return
			time.sleep(5)
			reps += 1

if __name__ == "__main__":
	# url = 'https://jrq5ug04de-dsn.algolia.net/1/indexes/*/queries?x-algolia-api-key=cbc84872f615adcc4d79c3b194e49c86&x-algolia-application-id=JRQ5UG04DE'
	url = 'https://jrq5ug04de-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(5.29.0)%3B%20Lite%20(5.29.0)%3B%20Browser%3B%20instantsearch.js%20(4.79.0)%3B%20react%20(17.0.2)%3B%20react-instantsearch%20(7.16.0)%3B%20react-instantsearch-core%20(7.16.0)%3B%20JS%20Helper%20(3.26.0)&x-algolia-api-key=cbc84872f615adcc4d79c3b194e49c86&x-algolia-application-id=JRQ5UG04DE'
	html = post_zenrows_html(url)

	products = []
	data_json = json.loads(html)
	for product in data_json['results'][0]['hits']:
		products.append('https://www.crocs.com'+product['url'])
	print(f"Found {len(products)} products")

	counter = 0
	counter_lock = threading.Lock()

	total = len(products)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(product_info, product) for product in products]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product datas {counter} / {total}", end="\r")

	print('\nDone')