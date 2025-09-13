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

write_filename = "final_officedepot_" + date_now + ".csv"
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

infos = []

def get_product_links(page):
    url = "https://pim-prod.odepotcloud.com/search"

    payload = json.dumps({
        "query": "brg_dyn_hlwrkgynh9",
        "brand": "od",
        "fl": "pid,url,price,description,brand,title,thumb_image,variants,Units,product_card_images,new_item,Hazmat,Eco~conscious,sku_reviews,sku_review_count,Diverse Supplier,Categories,Availability,default_nav_ids",
        "facetFilters": [],
        "rows": 24,
        "start": page,
        "browse": False,
        "sort": "relevance",
        "platform": "",
        "domainUrl": "",
        "isPunchout": False,
        "widgetId": "",
        "piqEnable": True,
        "isLoggedIn": False,
        "pppFlag": True,
        "inStockFilter": True,
        "BrUid2": "uid=1137077055070:v=15.0:ts=1756217250679:hc=8",
        "RequestType": "widget",
        "isSearchForInvalidCat": False,
        "retailerVisitorId": "0b199403-2562-4f7e-8e87-0bca1e622e95",
        "DynamicId": "brg_dyn_hlwrkgynh9",
        "DynamicName": "brg_dyn_hlwrkgynh9"
    })

    headers = {
        'authorization': 'Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ6aXBDb2RlIjoiOTgxMDEiLCJjZGFwU3RhdHVzIjoiWSIsImFwcGxJZCI6IiIsInNpZ25hdHVyZSI6InQzdW81IiwiaXNzIjoiT2ZmaWNlRGVwb3QiLCJpbnZMb2NEZnQiOiIxMDc4IiwiZ3NhQ3VzdG9tZXIiOiIiLCJjdXN0b21DYXRhbG9nSWQiOiIwIiwiYmlsbFRvSWQiOiIiLCJleHAiOjE3NTYzMDQyODEsImJyYW5kIjoiT0QiLCJqdGkiOiJKd3RJZCIsInpvbmVQcmljZSI6Ijc5MDEiLCJzaXRlVHlwZSI6IkoiLCJ1c2VySGFzaCI6IiIsImNvbnRhY3RJZCI6IiIsInNlc3Npb25IYXNoIjoiJDJhJDEwJE1tUUsuZ0MzaEtxejVrQTRkSHVnek9ockgwT0NnTXF3WkkwL3cuUmtCbEpSV3RvLkVxTDEuIiwic2Vzc2lvbklkIjoiMDE5MTE4MiIsInN0b3JlSWQiOiIiLCJzaHB0b1NlcURmdCI6IjAwMDEiLCJ1c2VySWQiOiIiLCJlbnZpcm9ubWVudCI6Im5vZGUxMyIsInNhbWVEYXlEZWxpdmVyeUVsaWdpYmxlQnlaaXBDb2RlIjoidHJ1ZSIsImN1c3RUeXBlIjoiIiwiS0VZX1VTRVJOQU1FIjoiVVNFUk5BTUUiLCJ1c2VyVHlwZSI6IlAiLCJwcmljZUNoYW5uZWwiOiIiLCJsb3lhbHR5TWVtYmVyVHlwZSI6IiJ9.wPIcrWZETuUYL5nIk-EaZ4skWPhyDS9P-_ddtjM2VJ1yn_TykKO_pd27zougMeI-9HmlfksuwTtt58ZiiCNcsA',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'x-api-key': 'TaCcwMhIj9aRaWDGpaivkaKAxA7rYe4f5k9Cm2Q8',
    }

    response = requests.post(url, headers=headers, data=payload)

    for item in response.json()['response']['response']['docs']:
        with counter_lock:
            item_no = item['brAttributes']['pid']
            price = item['cdapAttributes']['sellPrice']
            source_url = 'https://www.officedepot.com'+item['brAttributes']['url']
            infos.append([item_no, price, source_url])

def get_product_info(item_no, price, source_url):
    url = f"https://apps.bazaarvoice.com/bfd/v1/clients/OfficeDepot/api-products/cv2/resources/data/products.json?locale=en_US&allowMissing=true&apiVersion=5.4&filter=id%3A{item_no}"

    headers = {
        'bv-bfd-token': '2563,main_site,en_US',
        'origin': 'https://www.officedepot.com'
    }

    response = requests.get(url, headers=headers)

    for upc in response.json()['response']['Results'][0]['UPCs']:
        with counter_lock:
            with open(write_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([upc, price, source_url])

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = int(get_pages)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(infos)} product links\n')

	# infos = infos[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(infos)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, item_no, price, source_url) for item_no, price, source_url in infos]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')