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

write_filename = "final_publiclands_" + date_now + ".csv"
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
	}
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	url = f"https://prod-catalog-product-api.dickssportinggoods.com/v2/search?searchVO=%7B%22pageNumber%22%3A{page}%2C%22pageSize%22%3A144%2C%22selectedSort%22%3A5%2C%22selectedStore%22%3A%221419%22%2C%22storeId%22%3A%2216066%22%2C%22zipcode%22%3A%2298125%22%2C%22isFamilyPage%22%3Atrue%2C%22mlBypass%22%3Afalse%2C%22snbAudience%22%3A%22%22%2C%22includeFulfillmentFacets%22%3Afalse%2C%22selectedCategory%22%3A%2220310_10568377%22%7D"

	headers = {
		'accept': 'application/json, text/plain, */*',
		'accept-language': 'en-US,en;q=0.9',
		'channel': 'pl',
		'content-type': 'application/json',
		'disable-pinning': 'false',
		'origin': 'https://www.publiclands.com',
		'priority': 'u=1, i',
		'referer': 'https://www.publiclands.com/f/sale',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'cross-site',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'x-dsg-platform': 'v2',
		'Cookie': '_abck=01B05B3071D9EF511CC96544C027CC23~-1~YAAQatAuF5t4AwCZAQAAdjm4CQ4LdPcUhK7Nxt2ZtDTHu00l9TjyrA/YHGVEi3x+SS5z1RGRQTbyZ979lYM0nnwemxZs41iDj8JyCLJ0EIdzRMl1qYGSu49vt05ZrzoFJ4j0k5BGds5WpE5bEqmy9ln33PkHqIvjq1fz5VUoHVWB5Hko7UHwRBa3Hd1xXJuXcP1R0FpH8laY9IME17RfH+RxjYfcht2xfSA/xj4OCFiBhGV6LmkoDClGaIpJQiSH2xkzWW7wm1RxogSsIwjMdWjiy/qSe9fqQYg+eKN8h33Y+4HvVUYFqqraRo4dyr9Z5BI3yA59yUC81Kmx1pQbCe43qRQ74yxLu1fdLVCc5BCEEQZJ/L6r0RAgSysqkgWNgHRUGsgUN3DfPrXCiZvitm7cozaNqp4NR8bGpeeZ5lpiy/kv5AZMk9bxR8V9chefABcuZJE=~-1~-1~-1~~; bm_s=YAAQatAuF5x4AwCZAQAAdjm4CQQ8FaD7kQ/9gB7dgw+a4qgYO3dvGznkzqfp2bEhmoJLFNtUIohP0/pt6C7nx1NuYbDFnSnDyUtv50jCTui5EeU7MtJtqeFTj3fZEfeuUBgfAKiOKDndiVYfWZGrSOr2QY6mqtb5rfbBm/1F3E7/8aVphTXFnvSZTKw6ErQpDo3qVxu7Ug7ohQHWl/Mm9X1iobPUxhevZDQZFNhZKm733De9It2nOmTmeVwZmQA6iz1SXKE5jh9jOc/oMLG//XF1bw4aj55sQhodtFuw3ofi9ienlQmxGmbqOdSlsOon0965PqKPFrbOJr9GqmAngqBabYmfqoXE0aVESdaylWMgyGce2TbVbVSNn+ryyHtdAHYqbA2QHv7c6uoYoydKdSkWDwCCZYK2eOfQ/oRQrL6DVPdOJfO/TfcvjOEB3Ll+fL2KE4QuOxBIiQA+SNkHwOUjWxJSDV3i/Mj2iJKnJ0eiU3rbaXHPE/w4RYJ6g6jDBXsDd79OkaB9CGXPEG/TkG1GTl/g2sbLzWL2/0YDWZRAbAX6XcCdJeKY/+V8LsIks7SU; bm_ss=ab8e18ef4e; bm_sz=ABA520D6EA62414776B89E8B5EDE20E0~YAAQKxghF7FlDP+YAQAAIPSrCRxpipoXZ/vcOrI7VCCYzqBkftuipwGb8INZ7CQwV7PN3pfR/FW7K+bPLWZMnOUed00ruNS/BfDvuhhYtwr/fCcgimj73JgHVO4D2DHh0CWppTD1ywpJ/qnN4LiC2zVtWPHV/fPhe23P8IB0CTVdB+TB0N6p5uN/RNQhQ2e6y3d0J6EGGfLdtHE5PzA1YegvqLOKotGGrSY31+z9YjKcXMXscPFuB7BJssZMvGm5ACjnJ9ZNQi2Zg3Voefo0gUBCTJJSlDexpFkh4NVgo9ETRPisQzB3YRvKyd3j17eciZHEX9Gjxi8AMn615wT3UaQdqpRlDrlpGLIGN+okZOVhkIigoCc3x1xuVZnsWTiy1B/VpuLkf3JBHuKG~4272947~4403256'
	}

	response = requests.get(url, headers=headers)
	data_json = json.loads(response.text)

	for item in data_json['productVOs']:
		urls.append('https://www.publiclands.com'+item['assetSeoUrl'])

def get_product_info(url):
	html = get_zenrows_html(url)
	soup = BeautifulSoup(html, 'html.parser')

	print(soup.find('script', id='dcsg-ngx-pdp-server-state').get_text())

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/144)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
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