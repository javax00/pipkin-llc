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

write_filename = "final_bladehq_" + date_now + ".csv"
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

urls = []

def get_zenrows_html(target_url):
	# params = {
	# 	'apikey': ZENROWS_API_KEY,
	# 	'url': target_url,
	# 	'premium_proxy': 'true',
	# 	'proxy_country': 'us',
	# 	'js_render': 'true',
	# }
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	retry = 1
	while True:
		try:
			url = f'https://www.bladehq.com/cat--On-Sale--154?per_page=100&page={page}'
			headers = {
				'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
				'accept-language': 'en-US,en;q=0.9',
				'priority': 'u=0, i',
				'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
				'sec-ch-ua-mobile': '?0',
				'sec-ch-ua-platform': '"Windows"',
				'sec-fetch-dest': 'document',
				'sec-fetch-mode': 'navigate',
				'sec-fetch-site': 'none',
				'sec-fetch-user': '?1',
				'upgrade-insecure-requests': '1',
				'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
				'Cookie': 'guest_id=eyJpdiI6InhIZzRCdnpFeitkRU5WTWU2bnl4TVE9PSIsInZhbHVlIjoiU0xMWUZ5blRHc0svYjdOTE9ndDdvekl4ams1K3lWaXVVNmdtVDlZenNIY1hNZmNDYngrM1ZCVVhubTdZNUhUN094L2pRRGFCSzI2aWNZZzJtam5xeTl1VzRrazVxQzdyN3BpRDB3RkJKR0E9IiwibWFjIjoiZjMwYTU4YWU0OTUwYjg4MGI5ZGNjYmNhMWI0N2ZiN2YyZWUyOTFhNWIyNGQ3MDI1ZDliOGExMmY1NWMwN2RjZiIsInRhZyI6IiJ9; cart_id=109127709; cart_checksum=1V9jn20P36WonYqXazunScEhWm9zMb; _gcl_au=1.1.1845819279.1755150872; _isuid=F8D442DC-6794-4312-A090-CDE3ECC2EFFA; lantern=8150eecf-6158-43d2-9400-03a4e22c0112; __kla_id=eyJjaWQiOiJNR0poT0dFNU5EWXRNVEZoTXkwME1XWmhMVGc0Wm1NdFptUTNNekJqTkRObFpXTTQiLCIkcmVmZXJyZXIiOnsidHMiOjE3NTUxNTA4NzMsInZhbHVlIjoiaHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8iLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cuYmxhZGVocS5jb20vY2F0LS1Pbi1TYWxlLS0xNTQifSwiJGxhc3RfcmVmZXJyZXIiOnsidHMiOjE3NTYxODg1NzQsInZhbHVlIjoiIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vd3d3LmJsYWRlaHEuY29tL2NhdC0tT24tU2FsZS0tMTU0In19; cat_id=154; current_fragment_cat_id=154; _gid=GA1.2.85441335.1756985137; soundestID=20250904112537-lpaNJWKNMsjpOR3lmAfv6MOOw3sZKqTbMVLvThkMv5V2bZdxN; omnisendSessionID=4aKEIbxDrSiTJL-20250904112537; cf_clearance=7RGBbJdKh1UeU0o.9y9skVfViGgf1PqFkUlvGwXAbGA-1756985150-1.2.1.1-2Kp2NFc1T0jhoAD5os9yKAl8XN1Ys8cMmng4M7To7u9MKQyFbyMVMEojxcfHJURKaRwpKavVdiHvT3MlfylIfJ2x..orExrFM348h3GW._Z8v5t2TuT9nLVBt8CHsvy_wi2GN9j.W_MxfixyX6A0wq0VIl9c1O7oe_R7mqsX3yLOBXp0wbCtpEUrlkua4O7AsorKrI4MRFOj_rofks6vvN2GXN5aejDL5BrRPmENY9k; _gat_UA-2216859-49=1; _ga_SLPHVGKY7Y=GS2.1.s1756985137^$o4^$g1^$t1756985391^$j12^$l0^$h0; _ga=GA1.2.482631586.1755150872; _ga_MY6CC82HW6=GS2.2.s1756985138^$o4^$g1^$t1756985391^$j59^$l0^$h0; XSRF-TOKEN=eyJpdiI6IkN1bnltb2kwbG9ZeGVGNXpXV3R6THc9PSIsInZhbHVlIjoieE12YXhpUk9zWlJzOFovSy9RZ0NGV3JtQVN0U2l0V20yeCtiVWhOOFk1YjZjdDhZU3BFdmVxeGpLODZ6NXkxM2NMelNwemZBRVlUUTRKNGVlVmZXZSs4cUgwOWh4U0thWmVCc2dmdWtzMHAvRDBwRnluNWpQV0xnWXNYUUdCTEUiLCJtYWMiOiJmYjE0MjkwOTVkZTBlOThkOWQ5YjQwMGVlZTQ3N2E2YWVlZmNjNjYyNjcwYTMxMmVlMzY4OWU3M2RhOGUzZGM3IiwidGFnIjoiIn0%3D; laravel_session=eyJpdiI6IjBjZ0V3VUhuU0srVUd6OFNzWG1JWlE9PSIsInZhbHVlIjoiWC9oTTMwcm5WcGxIVEE4VUtrZmJGbzRPZXJFQS95ME1QT2NKSVFKTFdpYk1IbVZ1d29pYkxLbnY0RWp4Mys3TU1XR1JiYzREdU8vby9tU0RmQnFmM1FOK2tOeWRSS1J4YlFBNEovTGZVT2lYZnlCaWMyZlhFYk5jL29aY0poTWwiLCJtYWMiOiJhNTZmYWZhNjNmMWQ1Mzc1YmIwZjcyMjkxZjM1ZjllYWNmYjhhOTNiNWU0NTc2NzE3ZTAzN2FkZDEzNTQ0YWFkIiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6IlBmWnl3SXVUdldzaWFRSE4yK1lUQkE9PSIsInZhbHVlIjoidElxOXhZd3AyVVhkVWpOS3dqbVJNZHl5UW83UERFTTBmbnlJME5pOUtvUUZPbHAyOWxHaE5KREhrTnZYdWMvWTc3OFlmWnNBakY2b01ZZnBra1BaQ2xIWkdBbkFkYlZJWUpyRlhoeE9ZY1poTVFkbnpWZTF5cnZtblJwZDA0RmYiLCJtYWMiOiIxNWM3NmYxOWU0ZWJhNWRhODBlY2UyMzA0MTY3NDgyOWFmMmYxNDBjNjY2MTI4ZDE4NmVmN2VhYTMzMWFmNWYzIiwidGFnIjoiIn0%3D; cat_id=154; current_fragment_cat_id=154; laravel_session=eyJpdiI6ImUwUncweVJpT0ZLa1JBaHlITWF0R2c9PSIsInZhbHVlIjoiWjVUMWJaRjhJV2NmREI0VXRubVN1SS8yOTh0Q1RIWTlJWDJ5aXdFVEFSeENYMVVDbUV5NnM4bXBPNWgwSEN1SWMwalVnVzFIa0F3dVlxWTk2TTB1dVVNTm0ybmpsd0RjcHhJSU5CRmVseTRmM1hRSVZzbnFMbVBpdGZRbndCdFYiLCJtYWMiOiIxOTZkZDU0NmExODIxOWE4MGYwZTgyZTY2NTdkZDExNjMzNDBjMjA4Y2EyMjg4ZWFhMDU4ZjJiOTU4NWY0NzQwIiwidGFnIjoiIn0%3D'
			}

			response = requests.get(url, headers=headers)
			soup = BeautifulSoup(response.text, 'html.parser')

			for item in soup.find('div', class_='item-grid').find_all('div', class_='border-gray-200'):
				urls.append('https://www.bladehq.com'+item.find('a').get('href'))

			break
		except Exception as e:
			if retry == 3:
				return
			retry += 1
			time.sleep(5)
			print('Retrying...')

def get_product_info(link):
	retry = 1
	while True:
		try:
			headers = {
				'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
				'accept-language': 'en-US,en;q=0.9',
				'cache-control': 'max-age=0',
				'priority': 'u=0, i',
				'referer': 'https://www.bladehq.com/cat--On-Sale--154?per_page=100&page=2',
				'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
				'sec-ch-ua-mobile': '?0',
				'sec-ch-ua-platform': '"Windows"',
				'sec-fetch-dest': 'document',
				'sec-fetch-mode': 'navigate',
				'sec-fetch-site': 'same-origin',
				'sec-fetch-user': '?1',
				'upgrade-insecure-requests': '1',
				'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
				'Cookie': 'guest_id=eyJpdiI6InhIZzRCdnpFeitkRU5WTWU2bnl4TVE9PSIsInZhbHVlIjoiU0xMWUZ5blRHc0svYjdOTE9ndDdvekl4ams1K3lWaXVVNmdtVDlZenNIY1hNZmNDYngrM1ZCVVhubTdZNUhUN094L2pRRGFCSzI2aWNZZzJtam5xeTl1VzRrazVxQzdyN3BpRDB3RkJKR0E9IiwibWFjIjoiZjMwYTU4YWU0OTUwYjg4MGI5ZGNjYmNhMWI0N2ZiN2YyZWUyOTFhNWIyNGQ3MDI1ZDliOGExMmY1NWMwN2RjZiIsInRhZyI6IiJ9; cart_id=109127709; cart_checksum=1V9jn20P36WonYqXazunScEhWm9zMb; _gcl_au=1.1.1845819279.1755150872; _isuid=F8D442DC-6794-4312-A090-CDE3ECC2EFFA; lantern=8150eecf-6158-43d2-9400-03a4e22c0112; __kla_id=eyJjaWQiOiJNR0poT0dFNU5EWXRNVEZoTXkwME1XWmhMVGc0Wm1NdFptUTNNekJqTkRObFpXTTQiLCIkcmVmZXJyZXIiOnsidHMiOjE3NTUxNTA4NzMsInZhbHVlIjoiaHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8iLCJmaXJzdF9wYWdlIjoiaHR0cHM6Ly93d3cuYmxhZGVocS5jb20vY2F0LS1Pbi1TYWxlLS0xNTQifSwiJGxhc3RfcmVmZXJyZXIiOnsidHMiOjE3NTYxODg1NzQsInZhbHVlIjoiIiwiZmlyc3RfcGFnZSI6Imh0dHBzOi8vd3d3LmJsYWRlaHEuY29tL2NhdC0tT24tU2FsZS0tMTU0In19; cat_id=154; current_fragment_cat_id=154; _gid=GA1.2.85441335.1756985137; soundestID=20250904112537-lpaNJWKNMsjpOR3lmAfv6MOOw3sZKqTbMVLvThkMv5V2bZdxN; omnisendSessionID=4aKEIbxDrSiTJL-20250904112537; cf_clearance=7RGBbJdKh1UeU0o.9y9skVfViGgf1PqFkUlvGwXAbGA-1756985150-1.2.1.1-2Kp2NFc1T0jhoAD5os9yKAl8XN1Ys8cMmng4M7To7u9MKQyFbyMVMEojxcfHJURKaRwpKavVdiHvT3MlfylIfJ2x..orExrFM348h3GW._Z8v5t2TuT9nLVBt8CHsvy_wi2GN9j.W_MxfixyX6A0wq0VIl9c1O7oe_R7mqsX3yLOBXp0wbCtpEUrlkua4O7AsorKrI4MRFOj_rofks6vvN2GXN5aejDL5BrRPmENY9k; _gat_UA-2216859-49=1; _ga_SLPHVGKY7Y=GS2.1.s1756985137^$o4^$g1^$t1756985592^$j60^$l0^$h0; _ga=GA1.2.482631586.1755150872; _ga_MY6CC82HW6=GS2.2.s1756985138^$o4^$g1^$t1756985593^$j57^$l0^$h0; XSRF-TOKEN=eyJpdiI6ImdOZ1ppWHhHWXVXMVQrbVB3c3lSYVE9PSIsInZhbHVlIjoiY2VlS3cyNTVlYWlaTVd2b1pyWlZEK25oZnZvWEVibnJSZWhIYkptZkJXcVhXeFhVZk94TmY0MW5FL2JVL0FXalViOWNGTmdqOE9PS1kvTHc4VVlQczV1TlFWNWdodldTMWVPL3FITERQdjNtaWU0K05mSEJzeVE1c1FtTmRyVnMiLCJtYWMiOiI0MWMyZmI5ZTc3YTEyYzgxMjYzNGM4YjA3ZDhkOWE2MGVkZTYwY2YzNWI5MzY3YTEwZjE4YTc5ODA3NDMxMzZhIiwidGFnIjoiIn0%3D; laravel_session=eyJpdiI6Ik5kODl4cnhpN2dpUDJDZThSb0FjOVE9PSIsInZhbHVlIjoieGRBdldFUFgvM2dVU1ZPTWFlaFNJaldKMDV4Q3VxNElyYTBhQmJMWENOT3hLbFRKVHFuWlcwdERLcVgzOW1aYVQ3bUx1ODBtS0oxYyt2ajU2WW03N1c2MFJXK2M2Z3FWeWx6cEFWUzJKZzhKV3VKTm02d0FRVk55Y1VEcDhUNDciLCJtYWMiOiI4YmE0YzRmZWFlMjY3MzcwMTg5MDQxOGI2YzU2ZjgwOGQ2NGI1NTVhOTY3ZGQwYTAyNTIxYjZhOGIxNzdlYmY3IiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6IlRtaTR2MEVTdmZJL3k3MHlDVUx4WGc9PSIsInZhbHVlIjoiNmV0MEQzVHkyZUtiV0VkR1RPS0kxK0ZMcXJBM09KVnkzOUcwYnpNODRJbzhkZm9MUHhhcUx6Uy9ld2diT3pPTmdheFJkc3dZdFUwQm1JT2VXUlhNcHJVbWF0bjBHWmdjZ05UMURQZXM4aHlaYjNzZTZNcmZWRjdZeCtXSm1tSVIiLCJtYWMiOiJhNzA2NjU4Mjg3OGZlOWYxNmJjNDMzMmQwYmY1OTMyZGJiYzQ2ZmQ1ZmVjYzJmNGVlNzRkYTBhZTFiNzg0ODEwIiwidGFnIjoiIn0%3D; cat_id=154; current_fragment_cat_id=154; laravel_session=eyJpdiI6ImlFM1hNY1FISUJuV1dZOHFTbFlpNUE9PSIsInZhbHVlIjoiT0JBS25GaXFOclFjMk01NG9Nbjk2UFp2Y2ozemRNTkdJLzJBZkZkV2U3WlhGaGNBRW5rSzIvdXVma1dzcy9SNk1XSzF1ZWNkZkpiT3pyWGNoa3ZDMytobkFBNm55R2V3MXlTM1JmWGtTeDF4T0cyMUNKQmFVbjRSMnJ6YXFWb1oiLCJtYWMiOiI1ZDRlYWFhNDIxNjY0MmQwYTI1NGJlMjY5NWVhMjcyODgxYTQwNzRkYmI4ODg2YjAxY2Y5ZjJjMjk5MWZkNzE5IiwidGFnIjoiIn0%3D'
			}

			response = requests.get(link, headers=headers)
			soup = BeautifulSoup(response.text, 'html.parser')

			data_json = json.loads(soup.find('script', type='application/ld+json').get_text().replace('\n', ''))
			upc = data_json[0]['gtin']
			if not upc.isdigit():
				upc = ''
			elif len(upc) <= 10:
				upc = ''
			elif len(upc) == 11:
				upc = '00'+upc
			elif len(upc) == 12:
				upc = '0'+upc
			elif len(upc) == 14:
				upc = upc[1:]
			price = data_json[0]['offers']['price']

			with counter_lock:
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([upc, price, link])

			break
		except Exception as e:
			if retry == 3:
				return
			retry += 1
			time.sleep(5)
			print('Retrying...')

if __name__ == "__main__":
	get_pages = input('Enter total pages: ')

	total_pages = math.ceil(int(get_pages)/100)
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