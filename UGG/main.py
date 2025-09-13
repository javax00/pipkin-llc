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

write_filename = "final_ugg_" + date_now + ".csv"
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

def get_product_links(page):
	url = f'https://www.ugg.com/on/demandware.store/Sites-UGG-US-Site/en_US/Search-UpdateGrid?cgid=master-sale&start={page}&sz=36&selectedUrl=https%3A%2F%2Fwww.ugg.com%2Fon%2Fdemandware.store%2FSites-UGG-US-Site%2Fen_US%2FSearch-UpdateGrid%3Fcgid%3Dmaster-sale%26start%3D36%26sz%3D36'

	headers = {
		'accept': '*/*',
		'accept-language': 'en-US,en;q=0.9',
		'priority': 'u=1, i',
		'referer': 'https://www.ugg.com/master-sale/',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'same-origin',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'x-requested-with': 'XMLHttpRequest',
		'Cookie': 'dwanonymous_9e8dbed24c8074d91f36fc871b59b8d1=bdVoVkbKxOGN9Wplc8DcKwYvRa; dwac_93060b8fe2e218bf0e0765de0f=1SPZCtNgERLzfLTssPFElKqMfPvoMfTqIdg%3D|dw-only|||USD|false|US%2FPacific|true; cqcid=bdVoVkbKxOGN9Wplc8DcKwYvRa; cquid=||; sid=1SPZCtNgERLzfLTssPFElKqMfPvoMfTqIdg; __cq_dnt=0; dw_dnt=0; dwsid=AsR0joWESt8hf0Nn1_Hl431r0X--1a8n89smfUaULmjmpoSFpx_iQMRFuYtu_4j00JhxVXq7IjaUGyUOFd17ig==; _dyjsession=0k8cbgt786egetzhp2iiaml8a9tip3rj; dy_fs_page=www.ugg.com%2Fmaster-sale%2Fall-gender%2Bwomen; locale_pref=en_US; _fs_sample_user=true; coveo_visitorId=d88c75e1-a6a3-4d02-a308-41ac93acaacc; __pr.ajv=z6MDH3e1ii; tfc-l=%7B%22k%22%3A%7B%22v%22%3A%22g83pug6q6heib7jrcds5ksphpt%22%2C%22e%22%3A1817385931%7D%7D; apt_pixel=eyJkZXZpY2VJZCI6IjlkNGU0YjUwLTUwMTEtNDdhNi05NDk0LWVkNmU4OWM0NWY0NSIsInVzZXJJZCI6bnVsbCwiZXZlbnRJZCI6OSwibGFzdEV2ZW50VGltZSI6MTc1NjgwMjEzMjI1MywiY2hlY2tvdXQiOnsiYnJhbmQiOiJjYXNoYXBwYWZ0ZXJwYXkifX0=; _dy_soct=1756802220^!^!; utag_main=v_id:0199098bdbe5004329ec32d19f440506f003106701328^$_n:1^$_e:8^$_s:0^$_t:1756804021470^$ses_id:1756801784807%3Bexp-session^$_n:8%3Bexp-session^$_revpage:category%3Bexp-1756805821573^$productlist:Sale%3Bexp-session^$listid:master-sale%3Bexp-session^$dc_visit:1^$dc_event:2%3Bexp-session^$dc_region:us-west-2%3Bexp-session; datadome=j4Vdy6cWEj3BR571_emb8MQhiWIBhRSDz1Rrv4hF4Ka2cR9hcn8eQtXjlq8Z2Jh~CYQU4ezTb89AX0ofE16nbuAFMbYDkeHTRo2isz0gRP31~cr7cTHQhjGtbUQptEjk; forterToken=7de05f1253de417084b8a2bd28c2b2d1_1756802220719__UDF43-m4_23ck_; datadome=koDIpUzaSaj2TdRk~XChlYA3ubxNujz4n39TIBMi1ixxCZIcyfNzTcUUw8fL4UrMHTLiAnhGEsElXxzhNpNsa7Dew8zKz4pmBOMzWhHfH9E9hshFlECtAJDIz7LZkCN0; __cq_dnt=0; dw_dnt=0'
	}

	response = requests.get(url, headers=headers)
	soup = BeautifulSoup(response.text, 'html.parser')

	print(soup)

	for item in soup.find_all('div', class_='tile-row'):
		urls.append(item.find('div', class_='image-container').get('data-image-selector'))

def get_product_info(link):
	print(link)
	url = f"https://widget-api.stylitics.com/api/outfits?item_number={link}&locale=en-US&max=6&min=3&price_hide_double_zero_cents=false&profile=v3-classic&return_object=true&session_id=0767d325-6b84-49dd-b11c-f3ea27f9ab03&total=6&username=ugg&with_item_coords=true&exp.ugg.v3-hotspots=true&exp.ugg.pz-test=control&exp.ugg.v3-classic=true"

	headers = {
		'sec-ch-ua-platform': '"Windows"',
		'Referer': 'https://www.ugg.com/',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'Cookie': '__cf_bm=8Cdd5CaLU1qKZU58N0iPyk7AbtYpyzHhhbFK.3pnoHQ-1756802055-1.0.1.1-Xpp49rPZbzGtoawG16yIKKQbMA2D23rNxT5.9w6q1catyYtBkUI367XZBnUdPPepgWHJ2p6eqocjpqpIPmIGnQ8kKuLzObm2hMgGlpXQfOI'
	}

	response = requests.get(url, headers=headers)

	for item in response.json()['outfits'][0]['items']:
		source_url = item['affiliate_link']
		price = item['sale_price']
		color = item['retailer_color']
		for upc in item['skus']:
			upc = upc['upc']
			print(upc, price, color, source_url)


if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/36)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i*36) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(urls)} product links\n')

	urls = urls[:1]

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