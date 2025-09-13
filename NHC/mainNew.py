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

write_filename = "final_nhc_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variant', 'Promo', 'Source']
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

def get_product_links(page):
	# url = f"https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fherbs-etc&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fherbs-etc&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T"
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fhost-defense&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fhost-defense&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fjarrow&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fjarrow&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fspecial-offers%2Flane-coupon&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fspecial-offers%2Flane-coupon&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fbioptimizers&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fbioptimizers&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Flively-vitamin-co&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Flively-vitamin-co&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fspecial-offers%2Fmegafood&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fspecial-offers%2Fmegafood&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fpure-synergy&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fpure-synergy&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fderma-e&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fderma-e&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fenzymedica&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fenzymedica&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fspecial-offers%2Fnordic&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fspecial-offers%2Fnordic&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fpluscbd-oil&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fpluscbd-oil&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	# url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Fridgecrest-herbals&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Fridgecrest-herbals&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'
	url = f'https://www.nhc.com/app/extensions/RenewCo%20-%2021-1%20-%20NHC/SearchSpring/1.0.0/services/search.Service.ss?c=4902918&commercecategoryurl=%2Fbrand%2Ftrue-grace&consultLevel=0&country=US&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&domain=www.nhc.com%2Fbrand%2Ftrue-grace&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=search&include=facets&isloggedin=false&language=en&limit=32&matrixchilditems_fieldset=matrixchilditems_search&model=facetsModel&n=3&offset={page}&postman=false&priceLevelIds%5Bemployee%5D=4&priceLevelIds%5Bguest%5D%5Blist%5D=8&priceLevelIds%5Bguest%5D%5Bselling%5D=7&priceLevelIds%5Bmember%5D%5Blist%5D=10&priceLevelIds%5Bmember%5D%5Bselling%5D=9&priceLevelIds%5Bretail%5D%5Blist%5D=12&priceLevelIds%5Bretail%5D%5Bselling%5D=11&pricelevel=7&sort=commercecategory%3Adesc&ss_sessionId=db8e6533-12ed-4cb4-9357-e2131ff57cf3&ss_siteId=y11w6k&ss_userId=24b85b01-d3d1-42a5-b692-f0d4ffe1e390&use_pcv=T'

	response = requests.get(url)
	data_json = response.json()

	for item in data_json['items']:
		urls.append(item['_url'][1:])

def get_product_info(link):
	url = f'https://www.nhc.com/api/items?c=4902918&country=US&currency=USD&custitem_is_nhc_item=true&custitem_nhc_hide_from_website=false&facet.exclude=custitem_is_nhc_item%2Ccustitem_nhc_hide_from_website&fieldset=details&language=en&n=3&pricelevel=7&url={link}&use_pcv=T'
	response = requests.get(url)
	data_json = response.json()

	for item in json.loads(data_json['items'][0]['custitem_nhc_paid_search_json']):
		upc = item['gtin12']
		price = float(item['offers']['price'])*.9
		source_url = item['offers']['url']
		variant = item['name']
		promo = 'TG10'

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, variant, promo, source_url])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/32)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*32) for i in range(total_pages)]
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