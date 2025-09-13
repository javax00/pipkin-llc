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

write_filename = "final_5undergold_" + date_now + ".csv"
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
	r = requests.get(target_url, timeout=120)
	return r.text

def get_product_links(page):
	import requests

	url = f"https://search-api.jcpenney.com/v1/search-service/g/shops/shop-all-products?productGridView=medium&s1_deals_and_promotions=SALE&id=cat1007450013&cm_re=ZB-_-HOME-_-IM-_-LABOR-DAY-SALE-_-SHOP-NOW&page={page}&responseType=organic&geoZip=98188"

	headers = {
		'Cookie': 'Aurora=microservice; DP-Cloud-Origin=cloud6; DPCPT=|CP1N|CP2N|CP3N|CP4Y|CP5Y|CP6N|CP7N; UID=490bf9aca2d4d24700d; _abck=F65E63BACAF66753456DA55F8767E7A4~-1~YAAQb9AuFzsJy+6YAQAAYt6A9Q7jfiLfUkx3O3UAw4f5HFDXVQ6yDtA89bD5t9cI+5IZZ6VgOVq1fCDeVjfLKak8za4ufp2Roq0g44dYSIydXevexqq/N3RccbFLl/oddhZrjyyKar8S7JGFLdRl7Wk660QEHuDXBwJuPtfiHp9j+ZIhKqGGqcRCiPdOlCZfb3qxMH7W7AA4DVOUrTLgkhT7CBoh6fCXh68WhqQMvCGHs+PKHHAYg48iHcidtTyEX1qYNaBdpsxLRdeghZ5jkyAHRVyvmbcSRszxHuu0HU5edc8WNuU/BxWB3zGBfJuelkE61I785XBIaLeWMp7D02RmO0OKj4hdvbQTlfeLEVBg6WgH2zzSAkipNCHMQDMjzcveWiaR/AAmUcrqV1D6aE2Ekx0ZiFLjsb1to1TuXta8B1axZeSGhuTAwl8NmqTf2lLQUIbMskPgM2/CzJhq7W/IA+ybfumVJ44IFBCNRvc/fjT1bDBTg1EsqLxP94GiiZcWMKnojpwAEq2wH4iyH9TYE8h5jWx/cwbH5CTzCbnh4u9XHXOQNLqJyISraEz8dlVBDAV7ECqgEikyugGn4HZsMLDaOCFAg+YTKBinEzSF8kdyaDvJ/vNmAZ29KCyaW+wk4hsgHGzZ/T1d13Sap5V3+L91ia0caTc0F2eChMqYFeq0S6Qhp6ydiRPyGAR/P8FHD0LfvDsRQA7VHST4uOd7hqnwTJ0sMbEz/56+TQE0ctkn46LH4dZXIUveP2nhYxOBBSHZOi1a27scXlIz9VLbY/5k1R1cBCczaT7cqUEpM3+F8W5qMYDENfv/+bU/UY1K/s6QwQz8kh/U846165lJL9YrJFeeVN/gtnOHWMHZ79PILEhiIFUY/sBTv8cwjpf4h7Kf/tEglZqhTF21z5jMqwhU6JZckjxbw3N6FAXJ0kgvN3gO4Vw+R1nz/lt4BlraVefg6EWbqHO3+imEtWr6s5YxwEPrEkGgv4s=~-1~-1~-1~~; ak_bmsc=~~YAAQb9AuF5Jgy+6YAQAAgAKC9RyULzHjkRY+5rYibSw/HJ/KMQrW44nXHJuozCgUPGLCHAOBHH6FVybVDAPAtLOvxZgvflSjbhLyycxFmLVVe3FBvRVENWOfeM4Kh+ycbWpdC0CwuvQ+QAaSvDOvUgC2XwErOhHzwf104uX5T3XUwNKjpZGHaINHgUK+uL0b+sZkHuNSi8bU5g75xkRvYIwZFVdae7cP2ex9KJELJAo7mM7KTi8v/pweoj3zoOkT7Y06VOPGUPnAxi7CBO+zRq5kfsrFA5XVEiN6oBl0SyUK9js27ZEP+kxtLS0Jt5WSMmUuTaalpLqoG8ACSLZ0og0Y02RrpWS2aHb6mdZ98dXvKeUiTMmahOMCbCsR5NWZ; ak_geo=47.6115,-122.3343; bm_sv=90D0787DAAFE043C01B634284D5D956D~YAAQb9AuF70ty+6YAQAA3F6B9RyKmeCfXx3stcJhqvrAzwiVHUuMojeEkEXGvY7pTiPyDsgr67Kcby3QggX1bcvdXlC6FIqAT2CDF8PF5iRugt0yv/0uUSBLt93r5B/0JBzoHrvq+nob8+s9RuiClyMMI9/tel6ba2WFHUAR2cXj3MM1/8nSAI1D7e+9TOSb5OY6syHetSNIC2jKYut9N1nm8g44Frmuq/3XJvT6eb9nCODEdSPS4vj8XSm6NAX3qtsa~1; bm_sz=5342B80C7137F2F7CA653B8E536ABA31~YAAQb9AuF1buyu6YAQAAq2mA9RwFvfQ/mD7IWeGiavJNxqWKeberIf0nKw5qh05jmZpJ/saSssduJBCgIw3fZTX0CWkZ95M6qvQHkpAFDT6rhrpn/sdsYeMeb+CZaWmarQiV4Y3nK+Zfu6VUYovSHmunWAnDaPh/O8TkcNbm9G7BIQ+HWVhaHibYCMHGKTlFqp/VrobcvfciWkm8UmCHHe7mkwY4wHCX5NDlOTnK0e3pdcKvZPDxrAmufASWNAhTaMgGjQbP2SlPLLVGRDz1VuJ6y7hVUYrF6AMKWV3QtqpDgfWOeHgKDzm55jb5Y6+0u4dnWdqf7zUGbCyogedZ7M7kiOzWoUQhK2ZNDFHn~4404801~4604739'
	}

	response = requests.get(url, headers=headers, timeout=90)

	for item in response.json()['organicZoneInfo']['products']:
		urls.append('https://www.jcpenney.com'+item['pdpUrl'].split('?')[0])

def get_product_info(link):
	print(link)
	html = get_zenrows_html(link)
	soup = BeautifulSoup(html, 'html.parser')

	print(soup)
	# for script in soup.find_all('script', {'type': 'text/javascript'}):
	# 	if '__getYodaStaticRoute__' in script.get_text():
	# 		print('good')
	# 	break

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/48)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(1, total_pages+1)]
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