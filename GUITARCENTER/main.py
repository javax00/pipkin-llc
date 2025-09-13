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
import time

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_guitarcenter_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Color', 'Source Link']
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

def get_product_info(page):
    while True:
        try:
            target_url = "https://7aq22qs8rj-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(5.15.0)%3B%20Lite%20(5.15.0)%3B%20Browser%3B%20instantsearch.js%20(4.75.5)%3B%20react%20(18.3.1)%3B%20react-instantsearch%20(7.13.8)%3B%20react-instantsearch-core%20(7.13.8)%3B%20next.js%20(14.2.30)%3B%20JS%20Helper%20(3.22.5)&x-algolia-api-key=d04d765e552eb08aff3601eae8f2b729&x-algolia-application-id=7AQ22QS8RJ"

            payload = {
                "requests":[{
                    "indexName":"guitarcenter",
                    "analyticsTags":["Did Not Search"],
                    "facetFilters":["categoryPageIds:All Deals", "productCollections:All Deals"],
                    "facets":["*"],
                    "hitsPerPage":96,
                    "maxValuesPerFacet":10,
                    "numericFilters":["price>=1","price<=590","startDate<=1755501879"],
                    "page":page,
                    "query":"",
                    "ruleContexts":["collection-page"],
                    "userToken":"8072153612"
                }]
            }

            params = {
                "url": target_url,
                "apikey": ZENROWS_API_KEY,
                "premium_proxy": "true",
                "proxy_country": "us",
                "custom_headers": "true",
            }

            headers = {
                "Content-Type": "text/plain"
            }

            response = requests.post(zenrows_api, params=params, headers=headers, data=json.dumps(payload), timeout=90)

            for item in response.json()['results'][0]['hits']:
                price = item['price']
                source_link = 'https://www.guitarcenter.com'+item['seoUrl']

                upc = ''
                try:
                    upc = item['identifiers']['upccode']
                except:
                    pass


                color = ''
                try:
                    color = item['_highlightResult']['Color']['value']
                except:
                    pass

                with counter_lock:
                    with open(write_csv, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([upc, price, color, source_link])
            break
        except Exception as e:
            print(str(page) + ' - ' + str(e))
            time.sleep(5)
            pass

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/96)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\n\nDone.')
