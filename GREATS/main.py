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

write_filename = "final_greats_" + date_now + ".csv"
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
	r = requests.get(target_url)
	return r.text

def get_product_links():
    global urls
    url = "https://api.nosto.com/v1/graphql"

    payload = """
    query {
    products(
        limit: 250,
        filter: {
        availability: "InStock",
        tags1: [
            "YGroup_Royale2-0-mens",
            "YGroup_reignsliponmen",
            "YGroup_kingstonmen",
            "YGroup_royaleknit2.0women",
            "YGroup_reignsliponwomen",
            "YGroup_RoyaleKnit2.0-women",
            "YGroup_charliewomen",
            "YGroup_charliemen",
            "YGroup_royale2.0women",
            "YGroup_ironsidemen",
            "YGroup_royaleknit2.0men",
            "YGroup_reignmen",
            "YGroup_reignwomen",
            "YGroup_VarsityBomber",
            "YGroup_corsa-driver",
            "YGroup_Royale2-0-Slip-On-mens",
            "YGroup_royaleslipon2.0men",
            "YGroup_Parosmen",
            "YGroup_kingston",
            "YGroup_regent2.0men",
            "YGroup_charlie",
            "YGroup_Royale2-0-men",
            "YGroup_regent2.0women",
            "YGroup_corsadrivermen",
            "YGroup_corsa-drivermen",
            "YGroup_charlie-distressed-women"
        ]
        }
    ) {
        products {
        tags1
        }
    }
    }
    """

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': 'Basic OmdaaU1YZmR1eDB4TVBZeE0zZ0FjS1VydzlaT1pVb1d4OHM3R1ZTVW5TRUNvZmN5bXdseDlMMFdadHBYYXJmVjk=',
        'content-type': 'application/graphql',
        'origin': 'https://www.greats.com',
        'priority': 'u=1, i',
        'referer': 'https://www.greats.com/',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    for item in response.json()['data']['products']['products']:
        for var in item['tags1']:
            if '@' in var:
                url = 'https://www.greats.com/products/'+var.split(':')[1]
                if url not in urls:
                    urls.append(url)

def get_product_info(link):
	html = get_zenrows_html(link+'.json')
	data = json.loads(html)

	for variant in data['product']['variants']:
		upc = variant['barcode']
		price = variant['price']
		title = variant['title']
		source_link = link + '?variant=' + str(variant['id'])

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, title, source_link])

if __name__ == "__main__":
	get_product_links()

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