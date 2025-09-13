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

write_filename = "final_midwayusa_" + date_now + ".csv"
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

def get_product_links(page):
	url = "https://uqiwqhwtgq-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.14.2)%3B%20Browser%20(lite)&x-algolia-api-key=ba4f024807ab1f7f9d863f7d7ee61e7d&x-algolia-application-id=UQIWQHWTGQ"

	payload = {
		"requests": [
			{
			"userToken": "anonymous-d6f27541-5efb-4fd0-8cc9-b910737ae056",
			"indexName": "p_product",
			"query": "",
			"params": f"analytics=true&analyticsTags=[\"host:www\",\"feature:search\"]&attributesToHighlight=[]&attributesToRetrieve=[\"Availability\",\"colorCount\",\"familyId\",\"imagePath\",\"isBlemished\",\"descriptionGroup\",\"name\",\"New Products\",\"New Products\",\"promotionLink\",\"rebateLink\",\"rewardPointMultiplier\",\"Shipping\",\"swatches\",\"sku\",\"upc\",\"reviewRating\",\"numberOfReviews\",\"okToGridView\",\"promotionInventory\",\"promoSortOrder\",\"Discounts and Deals\",\"retail\"]&clickAnalytics=true&facetFilters=[[\"visible:true\"],[\"Discounts and Deals:Clearance\",\"Discounts and Deals:Sale\"],[\"Savings:25 - 50%\",\"Savings:50 - 75%\",\"Savings:More than 75%\",\"Savings:Up to 25%\"]]&facets=[\"Accuracy\",\"Action Type\",\"Active Ingredient\",\"Airgun Caliber\",\"Ammunition\", ... ]&hitsPerPage=60&maxValuesPerFacet=1000&numericFilters=[]&page={page}&responseFields=[\"facets\",\"hits\",\"nbHits\",\"userData\",\"query\",\"queryAfterRemoval\"]"
			},
			{
			"userToken": "anonymous-d6f27541-5efb-4fd0-8cc9-b910737ae056",
			"indexName": "p_product",
			"query": "",
			"params": "attributesToHighlight=[]&attributesToRetrieve=[]&facetFilters=[[\"visible:true\"],[\"Discounts and Deals:Clearance\",\"Discounts and Deals:Sale\"],[\"Savings:25 - 50%\",\"Savings:50 - 75%\",\"Savings:More than 75%\",\"Savings:Up to 25%\"]]&facetingAfterDistinct=true&facets=categoryLevelsNew&hitsPerPage=0&maxValuesPerFacet=1000&numericFilters=[]&responseFields=[\"facets\",\"nbHits\"]"
			},
			{
			"userToken": "anonymous-d6f27541-5efb-4fd0-8cc9-b910737ae056",
			"indexName": "p_product",
			"query": "",
			"params": "attributesToHighlight=[]&attributesToRetrieve=[]&facetFilters=[[\"visible:true\"],[\"Savings:25 - 50%\",\"Savings:50 - 75%\",\"Savings:More than 75%\",\"Savings:Up to 25%\"]]&facets=Discounts and Deals&hitsPerPage=0&maxValuesPerFacet=1000&numericFilters=[]&responseFields=[\"facets\"]"
			},
			{
			"userToken": "anonymous-d6f27541-5efb-4fd0-8cc9-b910737ae056",
			"indexName": "p_product",
			"query": "",
			"params": "attributesToHighlight=[]&attributesToRetrieve=[]&facetFilters=[[\"visible:true\"],[\"Discounts and Deals:Clearance\",\"Discounts and Deals:Sale\"]]&facets=Savings&hitsPerPage=0&maxValuesPerFacet=1000&numericFilters=[]&responseFields=[\"facets\"]"
			}
		]
	}

	headers = {
		'Accept': '*/*',
		'Accept-Language': 'en-US,en;q=0.9',
		'Connection': 'keep-alive',
		'Origin': 'https://www.midwayusa.com',
		'Referer': 'https://www.midwayusa.com/',
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
		upc = item['upc']
		if len(upc) == 12:
			upc = '0' + upc
		price = item['retail']['sortPrice']
		source_link = 'https://www.midwayusa.com/product/'+item['familyId']
		try:
			color = item['swatches'][0]['color']
		except:
			color = ''

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, color, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/60)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print('\nDone')
