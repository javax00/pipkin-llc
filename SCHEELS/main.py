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

write_filename = "final_scheels_" + date_now + ".csv"
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

def upc12_check_digit(upc11):
    upc11_str = str(upc11).zfill(11)
    if len(upc11_str) != 11 or not upc11_str.isdigit():
        raise ValueError("Input must be exactly 11 digits (as int or str).")
    digits = [int(x) for x in upc11_str]
    odd_sum = sum(digits[::2])
    even_sum = sum(digits[1::2])
    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10
    return f"{upc11_str}{check_digit}"

def get_product_links(page):
	target_url = "https://apihub.scheels.com/frontastic/action/algolia/search"
	payload = {
	"requests": [
		{
			"indexName": "Top Refinements",
			"params":
			{
				"filters": "false"
			}
		},
		{
			"indexName": "dynamic_facets",
			"params":
			{
				"filters": "type:category AND category:\"all\"",
				"hitsPerPage": 100
			}
		},
		{
			"indexName": "commercetools_products",
			"params":
			{
				"analyticsTags": ["www.scheels.com", "LoadMore"],
				"attributesToRetrieve": ["title", "variants.sku", "variants.images", "variants.inStock", "variants.attributes.refinementColor", "attributes.productBadge", "attributes.inStockStatus", "attributes.specialPricing", "attributes.discountMessage", "attributes.rebate", "attributes.isAmmo", "attributes.quantity", "isProductBundle", "image", "pricing.groups.default", "pricing.groups.canada", "pricing.minRetail", "swatchImages", "averageRating", "reviewCount", "primarySKU", "shop", "class", "subclass", "primaryCategory"],
				"clickAnalytics": True,
				"facetFilters": [
					["pricing.groups.default.onSale:true"],
					["categoryHierarchy.categories1:All"]
				],
				"facets": ["*"],
				"filters": "(inStock:true OR variants.attributes.comingSoon:true)",
				"getRankingInfo": True,
				"highlightPostTag": "__/ais-highlight__",
				"highlightPreTag": "__ais-highlight__",
				"maxValuesPerFacet": 1000,
				"page": page,
				"query": ""
			}
		},
		{
			"indexName": "commercetools_products",
			"params":
			{
				"analytics": False,
				"analyticsTags": ["www.scheels.com", "LoadMore"],
				"attributesToRetrieve": ["title", "variants.sku", "variants.images", "variants.inStock", "variants.attributes.refinementColor", "attributes.productBadge", "attributes.inStockStatus", "attributes.specialPricing", "attributes.discountMessage", "attributes.rebate", "attributes.isAmmo", "attributes.quantity", "isProductBundle", "image", "pricing.groups.default", "pricing.groups.canada", "pricing.minRetail", "swatchImages", "averageRating", "reviewCount", "primarySKU", "shop", "class", "subclass", "primaryCategory"],
				"clickAnalytics": False,
				"facetFilters": [
					["pricing.groups.default.onSale:true"]
				],
				"facets": ["categoryHierarchy.categories1"],
				"filters": "(inStock:true OR variants.attributes.comingSoon:true)",
				"getRankingInfo": True,
				"highlightPostTag": "__/ais-highlight__",
				"highlightPreTag": "__ais-highlight__",
				"hitsPerPage": 0,
				"maxValuesPerFacet": 1000,
				"page": 0,
				"query": ""
			}
		},
		{
			"indexName": "commercetools_products",
			"params":
			{
				"analytics": False,
				"analyticsTags": ["www.scheels.com", "LoadMore"],
				"attributesToRetrieve": ["title", "variants.sku", "variants.images", "variants.inStock", "variants.attributes.refinementColor", "attributes.productBadge", "attributes.inStockStatus", "attributes.specialPricing", "attributes.discountMessage", "attributes.rebate", "attributes.isAmmo", "attributes.quantity", "isProductBundle", "image", "pricing.groups.default", "pricing.groups.canada", "pricing.minRetail", "swatchImages", "averageRating", "reviewCount", "primarySKU", "shop", "class", "subclass", "primaryCategory"],
				"clickAnalytics": False,
				"facetFilters": [
					["categoryHierarchy.categories1:All"]
				],
				"facets": "pricing.groups.default.onSale",
				"filters": "(inStock:true OR variants.attributes.comingSoon:true)",
				"getRankingInfo": True,
				"highlightPostTag": "__/ais-highlight__",
				"highlightPreTag": "__ais-highlight__",
				"hitsPerPage": 0,
				"maxValuesPerFacet": 1000,
				"page": 0,
				"query": ""
			}
		}],
		"userToken": "GA1.1.3861943.1753260304"
	}

	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url
	}

	headers = {
		'Content-Type': 'text/plain'
	}

	try:
		# response = requests.post(
		# 	zenrows_url,
		# 	params=params,
		# 	data=json.dumps(payload),
		# 	headers=headers,
		# 	timeout=60
		# )
		response = requests.post(
			target_url,
			json=payload,
			headers=headers,
			timeout=60
		)
	except Exception as e:
		print(e)

	product = response.json()
	for item in product['results'][2]['hits']:
		price = item['pricing']['groups']['default']['minSale']
		source_link = 'https://www.scheels.com/p/'+item['primarySKU']
		for upcs in item['variants']:
			temp_upc = upcs['sku']
			upc = upc12_check_digit(temp_upc)

			for colors in item['swatchImages']:
				if str(temp_upc) in str(colors):
					color = colors['attributeValue']
					break

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, color, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')
	# MAX 1000 PRODUCTS ONLY

	total_pages = math.ceil(int(get_pages)/24)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(0, total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\n\nDone!')
