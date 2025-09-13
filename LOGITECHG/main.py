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

write_filename = "final_logitech_" + date_now + ".csv"
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
		'proxy_country': 'us'
	}
	r = requests.get(zenrows_api, params=params, timeout=60)
	return r.text

def get_zenrows_final(skus, auth):
	logi_api = 'https://www.logitechg.com/api/commerce/shopper-products/v1/organizations/f_ecom_bjdd_prd/products'
	params = {
		'ids': skus,
		'siteId': 'US'
	}

	logi_url_with_params = f"{logi_api}?{urlencode(params)}"

	zenrows_url = "https://api.zenrows.com/v1/"
	zenrows_params = {
		"apikey": ZENROWS_API_KEY,
		"url": logi_url_with_params,
		"custom_headers": "true",
		'js_render': 'true',
		"premium_proxy": "true",
	}

	headers = {
		"authorization": f"Bearer {auth}"
	}
	response = requests.get(zenrows_url, params=zenrows_params, headers=headers)
	json_data = json.loads(response.text)

	for product in json_data['data']:
		upc = '\''+product['ean']
		price = product['price']
		variant = product['c_color']
		source_link = product['c_url']

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, variant, source_link])

# eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmpkZF9wcmQiLCJraWQiOiIwYjFmODA0MC0wMjY2LTQyODYtODE3NS1iZDJhNWNmYzFlNTQiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1teWFjY291bnQucGF5bWVudGluc3RydW1lbnRzIHNmY2Muc2hvcHBlci1jdXN0b21lcnMubG9naW4gc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5vcmRlcnMgc2ZjYy5zaG9wcGVyLXByb2R1Y3RsaXN0cyBzZmNjLnNob3BwZXItY3VzdG9tLW9iamVjdHMgc2ZjYy5zaG9wcGVyLXByb21vdGlvbnMgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wYXltZW50aW5zdHJ1bWVudHMucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wcm9kdWN0bGlzdHMgY19nd3AtcHJvbW90aW9uc19yIGNfZ3Vlc3Qtb3JkZXJfciBjX3JlcXVlc3QtaW52b2ljZS5yIHNmY2Muc2hvcHBlci1jYXRlZ29yaWVzIHNmY2Muc2hvcHBlci1teWFjY291bnQgc2ZjYy5zaG9wcGVyLXByb2R1Y3RzIHNmY2Muc2hvcHBlci1teWFjY291bnQuYWRkcmVzc2VzIHNmY2Muc2hvcHBlci1teWFjY291bnQucncgc2ZjYy5wd2RsZXNzX2xvZ2luIHNmY2Muc2hvcHBlci1jdXN0b21lcnMucmVnaXN0ZXIgc2ZjYy5zaG9wcGVyLWJhc2tldHMtb3JkZXJzIGNfZ3Vlc3Qtb3JkZXIuciBzZmNjLnNob3BwZXItbXlhY2NvdW50LmFkZHJlc3Nlcy5ydyBzZmNjLnNob3BwZXItbXlhY2NvdW50LnByb2R1Y3RsaXN0cy5ydyBzZmNjLnNob3BwZXItYmFza2V0cy1vcmRlcnMucncgc2ZjYy5zaG9wcGVyLWdpZnQtY2VydGlmaWNhdGVzIGNfYnVzaW5lc3MtYWNjb3VudF9yIGNfY3VzdG9tZXItcHJvZHVjdHNfciBzZmNjLnNob3BwZXItcHJvZHVjdC1zZWFyY2ggc2ZjYy50c19leHRfb25fYmVoYWxmX29mIiwic3ViIjoiY2Mtc2xhczo6YmpkZF9wcmQ6OnNjaWQ6YTY1ZTc0YmUtOTAwZS00NThkLWFjM2ItNjc1ZWFlOWJiYzVhOjp1c2lkOmQ1M2M2NzA5LTUyNmEtNDQxYi1hMDZjLWUyNzMyNTMyOWZjNyIsImN0eCI6InNsYXMiLCJpc3MiOiJzbGFzL3Byb2QvYmpkZF9wcmQiLCJpc3QiOjEsImRudCI6IjAiLCJhdWQiOiJjb21tZXJjZWNsb3VkL3Byb2QvYmpkZF9wcmQiLCJuYmYiOjE3NTM4Njk1NTksInN0eSI6IlVzZXIiLCJpc2IiOiJ1aWRvOnNsYXM6OnVwbjpHdWVzdDo6dWlkbjpHdWVzdCBVc2VyOjpnY2lkOmFieGJzWHdYdzFrYklSbHJnMHdxWVlsYmRHOjpjaGlkOlVTIiwiZXhwIjoxNzUzODcxMzg5LCJpYXQiOjE3NTM4Njk1ODksImp0aSI6IkMyQy0xMDk5MDM0NTcwMTgwODc2NDc1MDMyNTQ0MzY1NzkzOTkyNTEwIn0.Cc3rCzhtADadQi1hlqTo-sS9jXcWlcwf_p897y8qQoYEJHii2crqsbeyPvU8KifzlUcWs5saip7sIBFg5uupdQ


if __name__ == "__main__":
	auth = input("Enter authorization: ")

	url = 'https://www.logitechg.com/en-us/gaming-sale.html#current-deals'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")

	skus = []
	products = soup.find('div', class_='plp-product-grid').find_all('div', class_='js-plp-product')
	for product in products:
		skus.append(product.find('div', class_='pangea-cmp').get('data-skus'))
	print(f'\nFound {len(skus)} products.\n')


	counter = 0
	counter_lock = threading.Lock()

	total = len(skus)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_zenrows_final, sku, auth) for sku in skus]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product datas {counter} / {total}", end='\r')

	print("\n\nDone")
