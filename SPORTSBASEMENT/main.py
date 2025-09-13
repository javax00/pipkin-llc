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

write_filename = "final_sportsbasement_" + date_now + ".csv"
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
	url = "https://04ie0383at-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.5.1)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.8.3)%3B%20JS%20Helper%20(3.2.2)&x-algolia-api-key=9ed10129c47364d3d9a37b6d381261b4&x-algolia-application-id=04IE0383AT"

	payload = {
		"requests": [
		{
			"indexName": "products",
			"params": f"hitsPerPage=48&clickAnalytics=true&facetingAfterDistinct=true&query=&maxValuesPerFacet=1000&highlightPreTag=%3Cspan%20class%3D%22ais-highlight%22%3E&highlightPostTag=%3C%2Fspan%3E&page={page}&distinct=true&filters=collection_ids%3A%22208197189704%22&ruleContexts=%5B%22deals%22%5D&facets=%5B%22named_tags.Discount%22%2C%22named_tags.Apparel%20Type%22%2C%22named_tags.Ski%20Type%22%2C%22named_tags.Snowboard%20Type%22%2C%22named_tags.Activity%22%2C%22named_tags.Gender%2FAge%22%2C%22named_tags.BreadcrumbType%22%2C%22vendor%22%2C%22options.size%22%2C%22named_tags.Bicycle%20Type%22%5D&tagFilters="
		}]
	}

	headers = {
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.9',
		'Connection': 'keep-alive',
		'Origin': 'https://shop.sportsbasement.com',
		'Referer': 'https://shop.sportsbasement.com/',
		'Sec-Fetch-Dest': 'empty',
		'Sec-Fetch-Mode': 'cors',
		'Sec-Fetch-Site': 'cross-site',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'content-type': 'application/x-www-form-urlencoded',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"'
	}

	response = requests.post(url, headers=headers, json=payload)

	for item in response.json()['results'][0]['hits']:
		urls.append('https://shop.sportsbasement.com/products/'+item['handle'])

def get_product_info(link):
	headers = {
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
		'accept-language': 'en-US,en;q=0.9',
		'cache-control': 'max-age=0',
		'if-none-match': '"cacheable:ecee62471d0222c401df6e7900c928b5"',
		'priority': 'u=0, i',
		'referer': 'https://shop.sportsbasement.com/collections/deals',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
		'sec-fetch-dest': 'document',
		'sec-fetch-mode': 'navigate',
		'sec-fetch-site': 'same-origin',
		'sec-fetch-user': '?1',
		'upgrade-insecure-requests': '1',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'Cookie': 'localization=US; cart_currency=USD; _shopify_y=c383c85e-86be-4cd2-ad21-8652b505973c; _orig_referrer=; _landing_page=%2Fcollections%2Fdeals; us_privacy=1YNN; _ALGOLIA=anonymous-ca4d2071-197a-45ee-8b87-865fb9bf0ef0; polaris_consent_settings={"clientId":"ec0dfe04-7f59-4746-9767-fba136cfecf5","implicit":true,"analyticsPermitted":true,"personalizationPermitted":true,"adsPermitted":true,"notOptedOut":true,"essentialPermitted":true}; _gcl_au=1.1.1319137620.1756112760; _ga=GA1.1.196234376.1756112760; swym-pid="TMd5BD52aVWhH5phCBA1bS6NuqfFyUUU5hqM8B491Rw="; swym-swymRegid="QOPPjdYvPLKNbP6k5TN0lhKSPCYdYq8PJDwJQVsGOvoT_eY5bfS-5qkT4R3yyRbBRIhkgRCyqxD5EfQsKpxP-_agI9hsH2xQwSHjmcD0XgKgb9B2mYSl-ykuKNy4pTPKdPOqwHhNJ67VynjxoQjR6LSdagQUoUzJvHC602UXQ-0"; swym-email=null; _hjSessionUser_1218721=eyJpZCI6ImMzMDU4MWQyLTdjZTctNWRhYy1hZjYxLTJkYzk2NDFhYzQ1NiIsImNyZWF0ZWQiOjE3NTYxMTI3NjY2MzUsImV4aXN0aW5nIjp0cnVlfQ==; checkout_continuity_service=7322304c-b9f9-4992-8039-63f13f1e50ef; tracker_device=7322304c-b9f9-4992-8039-63f13f1e50ef; __pr.1nre=pUxHM3G5ak; __kla_id=eyJjaWQiOiJaR0ZtTURKbE1tSXRZV1UzT0MwME9HTmlMV0l3TlRBdFlUa3lOMkUwWm1abU5tWXgiLCIkcmVmZXJyZXIiOnsidHMiOjE3NTYxMTI3NjQsInZhbHVlIjoiIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vc2hvcC5zcG9ydHNiYXNlbWVudC5jb20vY29sbGVjdGlvbnMvZGVhbHMifSwiJGxhc3RfcmVmZXJyZXIiOnsidHMiOjE3NTYxMTMyNTEsInZhbHVlIjoiIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vc2hvcC5zcG9ydHNiYXNlbWVudC5jb20vY29sbGVjdGlvbnMvZGVhbHMifX0=; _tracking_consent=3SPAM._USCA_t_t_eRrcuGUmRPKywnltQ3bhXg; _hjSession_1218721=eyJpZCI6ImQzZmE4ZmVmLTQ0YzYtNDllMy1iNGNlLTgxYzYyMmUxMWJkOCIsImMiOjE3NTY5ODA3ODQ3MTMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MX0=; swym-session-id="pysjzhxij9hhneuwk0sextert3w6uor9u8bwq0tfz49kmvp17g1nma3ca9qhbrml"; swym-v-ckd=1; swym-o_s={"mktenabled":false}; _shopify_s=7fcb201f-2608-433b-8ae7-f34e7e3a9174; _ga_2HRDLG9H77=GS2.1.s1756980781^$o3^$g1^$t1756981724^$j19^$l0^$h1520982463; _ga_4JTEZMGK4J=GS2.1.s1756980783^$o3^$g1^$t1756981724^$j19^$l0^$h0; _ga_W2XFDLGK73=GS2.1.s1756980783^$o2^$g1^$t1756981724^$j19^$l0^$h0; _ga_Z1C97N01BT=GS2.1.s1756980783^$o3^$g1^$t1756981724^$j19^$l0^$h0; _shopify_essential=:AZjgeeY3AAEAd2Z8nmjBvV6gMrZEIcd6oxkVFKxphxTx5gkdnv6zG0aIkNJ8wAugVusbNV5QAH1CNHYVydPbbNdR9SpsVsVRRgUFHybenLJ97L4V97u-ZVM:; keep_alive=eyJ2IjoyLCJ0cyI6MTc1Njk4MjM3MjE4NywiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjoyNiwiY2EiOjAsImthIjowLCJzYSI6Miwia2JhIjowLCJ0YSI6MCwidCI6NjQ3LCJubSI6MSwibXMiOjAuMTMsIm1qIjozLjE5LCJtc3AiOjIuMTMsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAsInNqIjowLCJzc20iOjAsInNwIjowLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6MTAsInMiOjE3NTY5ODA3ODA1NDEsImQiOjE1MzV9fQ%3D%3D; _landing_page=%2Fproducts%2Ftopside-chambray-standard; _orig_referrer=https%3A%2F%2Fshop.sportsbasement.com%2F; _shopify_s=7fcb201f-2608-433b-8ae7-f34e7e3a9174; _shopify_y=c383c85e-86be-4cd2-ad21-8652b505973c; _tracking_consent=3.AMPS_USCA_t_t_1SPle0BiTc-GOC2Wom484w; _shopify_essential=:AZjgeeY3AAEAEPqFzSdJxqn_VGVakkO6iV0MDhoJHU7hWl4le9sj3WUPVB_rQ3WkhU2JH8eiR00bseox8Csq75_C4YXbtv1tgSvJWaSiCFWjwLUMfl6W:; cart_currency=USD; keep_alive=eyJ2IjoyLCJ0cyI6MTc1Njk4MjM3MjE4NywiZW52Ijp7IndkIjowLCJ1YSI6MSwiY3YiOjEsImJyIjoxfSwiYmh2Ijp7Im1hIjoyNiwiY2EiOjAsImthIjowLCJzYSI6Miwia2JhIjowLCJ0YSI6MCwidCI6NjQ3LCJubSI6MSwibXMiOjAuMTMsIm1qIjozLjE5LCJtc3AiOjIuMTMsInZjIjowLCJjcCI6MCwicmMiOjAsImtqIjowLCJraSI6MCwic3MiOjAsInNqIjowLCJzc20iOjAsInNwIjowLCJ0cyI6MCwidGoiOjAsInRwIjowLCJ0c20iOjB9LCJzZXMiOnsicCI6MTAsInMiOjE3NTY5ODA3ODA1NDEsImQiOjE1MzV9fQ%3D%3D; localization=US'
	}

	prod_page = requests.get(link, headers=headers)
	soup = BeautifulSoup(prod_page.text, 'html.parser')

	from_page = {}
	for script in soup.find_all('script'):
		if 'POWERREVIEWS.display.render(' in script.get_text():
			raw_data = script.get_text().strip().replace('POWERREVIEWS.display.render(', '').replace(');', '')
			fixed = re.sub(r'(\s*)(\w+):', r'\1"\2":', raw_data)
			fixed = fixed.replace("'", '"')
			fixed = re.sub(r'""(https?)":', r'"\1":', fixed)
			fixed = fixed.replace('https"', 'https')
			fixed = fixed.replace(',\n        }', '\n        }')
			fixed = fixed.replace(',\n        ]', '\n        ]')
			fixed = fixed.replace(',\n}', '\n}')
			fixed = fixed.replace(',\n]', '\n]')
			data1 = json.loads(fixed)
			
			for upcs in data1['product']['variants']:
				from_page[upcs['page_id_variant']] = upcs['upc']
			break

	##########################################################

	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = from_page[str(variant['id'])]
		if not upc.isdigit():
			upc = ''
		elif len(upc) <= 10:
			upc = ''
		elif len(upc) == 11:
			upc = '00'+upc
		elif len(upc) == 12:
			upc = '0'+upc
		elif len(upc) == 14:
			upc = upc[1:]
		price = variant['price']
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
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