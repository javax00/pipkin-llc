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

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_castore_" + date_now + ".csv"
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
		# 'proxy_country': 'us',
		'js_render': 'true',
	}
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	global urls
	# url = f'https://services.mybcapps.com/bc-sf-filter/filter?_=pf&t=1754472841262&sid=a6becf65-66d4-9ab7-ebf4-7535cd1b3abc&shop=castoretest.myshopify.com&page={page}&limit=24&sort=manual&locale=en&event_type=init&pg=collection_page&build_filter_tree=true&collection_scope=261839683721&money_format=%26%2336%3B%7B%7Bamount%7D%7D&money_format_with_currency=%26%2336%3B%7B%7Bamount%7D%7D+USD&widgetId=eI58ftp8wx%2Fthemes%2Fdefault%2Fmain__0__liquid&viewAs=grid--3&device=&first_load=true&productImageWidth=550&productPerRow=3&widget_updated_at=1754320299&templateId=eI58ftp8wx&current_locale=&simplifiedIntegration=false&customer_id=d80221ab-6328-4746-8ec7-b4af69b98eb4&return_all_currency_fields=false&currency_rate=1.36269&currency=USD&country=US&search_no_result=true&sort_first=available&product_available=true&variant_available=true'
	# url = f'https://services.mybcapps.com/bc-sf-filter/filter?_=pf&t=1755847685654&sid=3005f6a9-99ce-3e23-b7c3-b98163dcbdb1&shop=castoreus.myshopify.com&page={page}&limit=24&sort=manual&locale=en&event_type=init&pg=collection_page&build_filter_tree=true&collection_scope=289159086246&money_format=%26%2336%3B%7B%7Bamount%7D%7D&money_format_with_currency=%26%2336%3B%7B%7Bamount%7D%7D+USD&viewAs=grid--4&device=&first_load=false&productImageWidth=450&productPerRow=4&widget_updated_at=1755007015&templateId=TGiLieXa4W&current_locale=&simplifiedIntegration=false&customer_id=d80221ab-6328-4746-8ec7-b4af69b98eb4&return_all_currency_fields=false&currency_rate=1.0&currency=USD&country=US&isMobile=false&isTabletPortraitMax=false&behavior=refresh&tag=&sort_first=available&product_available=true&variant_available=true'
	url = f'https://services.mybcapps.com/bc-sf-filter/filter?_=pf&t=1756458167616&sid=7b7444ce-4086-4ac0-bee1-afa1140633a1&shop=castoretest.myshopify.com&page={page}&limit=24&sort=manual&locale=en&event_type=init&pg=collection_page&build_filter_tree=true&collection_scope=292161224841&money_format=%26%2336%3B%7B%7Bamount%7D%7D&money_format_with_currency=%26%2336%3B%7B%7Bamount%7D%7D+USD&viewAs=grid--3&device=&first_load=false&productImageWidth=550&productPerRow=3&widget_updated_at=1756301625&templateId=eI58ftp8wx&current_locale=&simplifiedIntegration=false&customer_id=d80221ab-6328-4746-8ec7-b4af69b98eb4&return_all_currency_fields=false&currency_rate=1.38399&currency=USD&country=US&isMobile=false&isTabletPortraitMax=false&behavior=refresh&tag=&sort_first=available&product_available=true&variant_available=true'
	html = get_zenrows_html(url)
	data = json.loads(html)

	for prod in data['products']:
		for variant in prod['variants']:
			upc = variant['barcode']
			if not upc.isdigit():
				upc = ''
			price = variant['price']
			title = variant['title']
			souce_url = 'https://castore.com/products/'+prod['handle']+'?variant='+str(variant['id'])

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, title, souce_url])

if __name__ == "__main__":
	get_prods = input('Enter total products: ')

	total_pages = math.ceil(int(get_prods) / 24)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\nDone')