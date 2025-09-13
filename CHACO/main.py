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

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'				#
load_dotenv(dotenv_path=env_path)										#
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')							#
if not ZENROWS_API_KEY:													#
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")	#
zenrows_api = 'https://api.zenrows.com/v1/'								#
############################## ZENROWS ##################################

write_filename = "chaco_product_urls_" + date_now + ".csv"
write_headers = ['URLs']
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

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us'
	}
	r = requests.get(zenrows_api, params=params, timeout=60)
	return r.text

def get_page_links(page):
	url = f'https://www.chacos.com/US/en/sale-summer-annual-sale-extra-30-off/?start={page * 48}&sz=48'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")

	links = soup.find('ul', id='search-result-items').find_all('li')
	for link in links:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([link.find("meta", itemprop="url").get("content")])

if __name__ == "__main__":
	url = 'https://www.chacos.com/US/en/sale-summer-annual-sale-extra-30-off/'
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, "html.parser")
	total_page = int(soup.find('div', class_='product-result-count').text.strip().split(' ')[0])
	total_page = math.ceil(total_page / 48)

	for i in range(0, total_page):
		print(f"Processing page {i+1} / {total_page}")
		get_page_links(i)
	
	print('Done')