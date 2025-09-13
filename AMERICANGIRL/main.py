import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import math
from datetime import datetime
import json
import html

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "final_american_girl_" + date_now + ".csv"
write_headers = ['UPC','Price','Source Link']
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

if __name__ == "__main__":
	pages = 1
	while True:
		# url = 'https://nwq1tg.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Famerican-girl-last-chance&resultsFormat=native&siteId=nwq1tg&resultsPerPage=60&includedFacets=&bgfilter.collection_handle=american-girl-last-chance&page='+str(pages)
		# url = 'https://nwq1tg.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Famerican-girl-last-chance%23page%3D2&resultsFormat=native&siteId=nwq1tg&resultsPerPage=60&includedFacets=&bgfilter.collection_handle=american-girl-last-chance&page='+str(pages)
		# url = 'https://nwq1tg.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Flabor-day-sale&resultsFormat=native&siteId=nwq1tg&resultsPerPage=60&includedFacets=&bgfilter.collection_handle=labor-day-sale&page='+str(pages)
		# url = 'https://nwq1tg.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Famerican-girl-last-chance&resultsFormat=native&siteId=nwq1tg&resultsPerPage=60&includedFacets=&bgfilter.collection_handle=american-girl-last-chance&page='+str(pages)
		url = 'https://nwq1tg.a.searchspring.io/api/search/search.json?domain=%2Fcollections%2Fnew-to-sale&resultsFormat=native&siteId=nwq1tg&resultsPerPage=60&includedFacets=&bgfilter.collection_handle=new-to-sale&page='+str(pages)
		res = requests.get(url, timeout=60)
		json_data = json.loads(res.text)

		if json_data['results'] == []:
			print("No results found.\nDone.")
			break
		else:
			print('Scraping page: ' + str(pages))

			for result in json_data['results']:
				upc_raw = result['mfield_en_us_payload']

				if re.search(r'&quot;pla_upc&quot;\s*:\s*&quot;(\d+)&quot;', upc_raw) != None:
					upc = re.search(r'&quot;pla_upc&quot;\s*:\s*&quot;(\d+)&quot;', upc_raw).group(1)
				else:
					upc = ''
				price = result['price']
				url = 'https://www.americangirl.com'+result['url']
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, url])
		pages += 1
	