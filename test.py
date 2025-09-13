from dotenv import load_dotenv
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get ZenRows API key from environment variables
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")

# Get ZenRows API key from environment variables
keepa_api_key = os.getenv('KEEPA_API_KEY')
if not keepa_api_key:
    raise ValueError("Please set KEEPA_API_KEY in your .env file")

zenrows_api = "https://api.zenrows.com/v1/"












# import os
# import csv
# import requests
# from dotenv import load_dotenv
# from pathlib import Path
# from bs4 import BeautifulSoup
# from urllib.parse import urlencode
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import threading
# import json
# import concurrent.futures
# import math
# from datetime import datetime

# date_now = str(datetime.now().strftime("%m_%d_%Y"))
# ############################## ZENROWS ##################################
# env_path = Path(__file__).resolve().parent.parent / '.env'				#
# load_dotenv(dotenv_path=env_path)										#
# ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
# if not ZENROWS_API_KEY:													
# 	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
# zenrows_api = 'https://api.zenrows.com/v1/'								#
# ############################## ZENROWS ##################################

# write_filename = "final_chaco_" + date_now + ".csv"
# write_headers = ['UPC', 'Price', 'Variant', 'Source Link']
# ############################# CSV WRITE #################################
# script_dir = os.path.dirname(os.path.abspath(__file__))					#
# write_csv = os.path.join(script_dir, write_filename)					#
# if os.path.exists(write_csv):											#
# 	os.remove(write_csv)												#
# 	print(f"Deleted existing file: {write_csv}\nStarting now...\n")		#
# 																		#
# with open(write_csv, 'w', newline='', encoding='utf-8') as f:			#
# 	writer = csv.writer(f)												#
# 	writer.writerow(write_headers)										#
# ############################# CSV WRITE #################################

# read_filename = "product_urls_chaco_" + date_now + ".csv"
# ############################# CSV READ ##################################
# script_dir = os.path.dirname(os.path.abspath(__file__))     			#
# read_csv = os.path.join(script_dir, read_filename) 						#
# 																		#
# products = []															#
# with open(read_csv, 'r', encoding='utf-8') as f:						#
# 	reader = csv.reader(f)												#
# 	header = next(reader)												#
# 	for row in reader:													#
# 		products.append(row)											#
# ############################# CSV READ ##################################

# def get_zenrows_html(target_url):
# 	params = {
# 		'apikey': ZENROWS_API_KEY,
# 		'url': target_url,
# 		'premium_proxy': 'true',
# 		'js_render': 'true',
# 		'proxy_country': 'us'
# 	}
# 	r = requests.get(zenrows_api, params=params, timeout=60)
# 	return r.text

# if __name__ == "__main__":
# 	url = ''
# 	html = get_zenrows_html(url)


# ####################################### NUMBER RANGE ########################################
# 	counter = 0
# 	counter_lock = threading.Lock()

# 	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
# 		futures = [executor.submit(get_product_info, i, total_pages) for i in range(total_pages)]
# 		# Optional: Wait for all threads to finish
# 		concurrent.futures.wait(futures)


# ####################################### LIST ########################################
# 	counter = 0
# 	counter_lock = threading.Lock()

# 	total = len(skus)

# 	with ThreadPoolExecutor(max_workers=50) as executor:
# 		futures = [executor.submit(get_zenrows_final, sku, auth) for sku in skus]
# 		for future in as_completed(futures):
# 			with counter_lock:
# 				counter += 1
# 				print(f"Getting product datas {counter} / {total}", end='\r')






##################################################
########### FIND UPC USING UPCITEMDB #############
##################################################
# import requests
# import random
# import time
# from bs4 import BeautifulSoup

# keyword = "PROL-WU8 Booty Call"

# target_url = f"https://api.upcitemdb.com/prod/trial/search?s={keyword}"
# zenrows_url = "https://api.zenrows.com/v1/"

# params = {
#     'url': target_url,
#     'apikey': ZENROWS_API_KEY,
#     'premium_proxy': 'true',
#     'proxy_country': 'us',
# }

# r = requests.get(zenrows_url, params=params, timeout=30)
# print(r.text)

# if 'RESP002' in r.text:
#     print('No data')
# else:
#     data = r.json()
#     for item in data["items"]:
#         print(item['ean'])
#         print(item['color'])
#         print(item['size'])
#         print()


# # # upc_list = [item["ean"] for item in data["items"]]
# # # print(upc_list)



##################################################
############ FIND UPC USING KEEPA ################
##################################################

# import requests
# import re

# keyword = 'Carhartt 102080 - Women\'s Rugged Flex® Loose Fit Canvas Work Pant'

# url = "https://api.keepa.com/search"
# params = {
#     "key": keepa_api_key,
#     "domain": 1,
#     "type": "product",
#     "term": keyword,
#     "perPage": 5,
#     "page": 0
# }

# res = requests.get(url, params=params).json()

# for prod in res.get("products", []):
#     print(prod["asin"], "-", prod.get("title"))

#####################################

# import urllib.parse
# keepa_url = "https://api.keepa.com/search"

# keepa_query = {
#     "key": KEEPA_API_KEY,
#     "domain": 1,
#     "type": "product",
#     "term": name,
#     "perPage": 5,
#     "page": 0,
#     "selection": "title",
#     "sort": "title"
# }

# target_url = keepa_url + "?" + urllib.parse.urlencode(keepa_query)

# params = {
#     'apikey': ZENROWS_API_KEY,
#     'url': target_url,
#     'premium_proxy': 'true',
#     'proxy_country': 'us',
#     'wait': '5000',
# }

# r = requests.get(zenrows_api, params=params, timeout=90)
# res = r.json()

# for prod in res.get("products", []):
#     with counter_lock:
#         asin = prod["asin"]
#         with open(write_csv, 'a', newline='', encoding='utf-8') as f:
#             writer = csv.writer(f)
#             writer.writerow([asin, price, url])

#####################################

# import requests
# import json

# # Step 1: Download the JSON data from the URL
# url = "https://www.vincecamuto.com/collections/buy-more-save-more-event/products/vince-camuto-calie-braided-flat-loafer-lux-silver"
# response = requests.get(url+'.json')
# data = response.json()

# # Step 2: Loop through each variant and print the barcode
# for variant in data['product']['variants']:
#     print(variant['barcode'])
#     print(variant['price'])
#     print(variant['title'])
#     print(url)
#     print('~~~~~~~~~~~~~~~~~~~~~~')

#####################################

# import requests
# import random
# import time
# import  json
# from bs4 import BeautifulSoup


# target_url = "https://www.healthydirections.com/product-categories/catalog-limited-offer?key=410516"
# zenrows_url = "https://api.zenrows.com/v1/"

# params = {
#     'url': target_url,
#     'apikey': zenrows_api_key,
#     'premium_proxy': 'true',
#     'proxy_country': 'us',
#     'js_render': 'true',
#     'antibot': 'true',
# }

# r = requests.get(zenrows_url, params=params, timeout=90)
# time.sleep(2)
# if r.headers.get("Content-Type", "").startswith("application/json"):
#     print(r.text)  # Print error message
# else:
#     soup = BeautifulSoup(r.text, "html.parser")

# with open("downloaded_page.html", "w", encoding="utf-8") as f:
#     f.write(soup.prettify())

#####################################


# import json

# # Open and load the JSON file
# with open('14 - NIKE/a.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)

# # Pretty-print to console
# print(json.dumps(data, indent=2, ensure_ascii=False))

# # Save prettified JSON to b.json
# with open('14 - NIKE/b.json', 'w', encoding='utf-8') as f:
#     json.dump(data, f, indent=2, ensure_ascii=False)


#####################################

# # pip install requests
# import requests

# url = 'https://www.nike.com/t/cosmic-runner-baby-toddler-shoes-Ua3qA0Nz/HM4401-001'
# apikey = '8904f93054e642f7d1961ad222f4a45703d16b34'
# params = {
#     'url': url,
#     'apikey': apikey,
# 	'js_render': 'true',
# 	'premium_proxy': 'true',
# }
# response = requests.get('https://api.zenrows.com/v1/', params=params)
# print(response.text)

################################################


# # 11 UPC TO 12 UPC
# upc11 = 13620460832
# digits = [int(x) for x in str(upc11)]
# if len(digits) != 11:
#     raise ValueError("Input must be 11 digits")
# odd_sum = sum(digits[::2])
# even_sum = sum(digits[1::2])
# total = (odd_sum * 3) + even_sum
# check_digit = (10 - (total % 10)) % 10
# print(f"{upc11}{check_digit}")

#################### BY BATCHHHHHHHHHHHHHHHHHHH

# import pandas as pd
# import os

# # Edit this to your CSV file name
# csv_filename = "macys_final_07_28_2025.csv"

# # How many rows per file
# rows_per_file = 99999

# # Get base file name without extension
# base_name, ext = os.path.splitext(csv_filename)

# # Read the entire CSV file
# df = pd.read_csv(csv_filename)

# # Calculate number of split files
# num_files = (len(df) + rows_per_file - 1) // rows_per_file

# for i in range(num_files):
#     start = i * rows_per_file
#     end = min((i + 1) * rows_per_file, len(df))
#     split_df = df.iloc[start:end]
#     split_filename = f"{base_name} - {i+1}{ext}"
#     split_df.to_csv(split_filename, index=False)
#     print(f"Saved: {split_filename}")

# print("Done!")

##################################################################

# import requests
# import json

# url = "https://7cuhthvkmm-dsn.algolia.net/1/indexes/prod_rackroom_products_v1/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.24.0)%3B%20Browser"

# payload = "{\"query\":\"\",\"hitsPerPage\":90,\"facets\":[\"*\"],\"facetFilters\":[[\"categoryPageId:onsale\"]],\"page\":\"0\",\"clickAnalytics\":true}"
# headers = {
#     'Accept': '*/*',
#     'content-type': 'application/x-www-form-urlencoded',
#     'x-algolia-api-key': '0ace919e79993a4530700d0b32a1c429',
#     'x-algolia-application-id': '7CUHTHVKMM'
# }

# response = requests.post(url, headers=headers, data=payload)

# for item in response.json()['hits']:
#     print(item['vendorUpc'])
#     print(item['price'])
#     print(item['colors'][0])
#     print('https://www.rackroomshoes.com/p/'+str(item['sku']))
#     print()

# import requests
# import json

# target_url = "https://prod-catalog-product-api.dickssportinggoods.com/v2/search?searchVO=%7B%22pageNumber%22%3A0%2C%22pageSize%22%3A144%2C%22selectedSort%22%3A5%2C%22selectedStore%22%3A%221419%22%2C%22storeId%22%3A%2215108%22%2C%22zipcode%22%3A%2298125%22%2C%22isFamilyPage%22%3Atrue%2C%22mlBypass%22%3Afalse%2C%22snbAudience%22%3A%22%22%2C%22includeFulfillmentFacets%22%3Afalse%2C%22selectedCategory%22%3A%2212301_10598220%22%7D"

# username = "customer-Andrew_1WwJD-cc-US"
# password = "AmazonPacific1++"
# proxy = f"http://{username}:{password}@pr.oxylabs.io:7777"

# proxies = {
#     "http": proxy,
#     "https": proxy,
# }

# r = requests.get(target_url, proxies=proxies, timeout=90)
# print(r.json())
