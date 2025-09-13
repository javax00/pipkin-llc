from ast import excepthandler
import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import threading
import json
import concurrent.futures
import math
import time
from datetime import datetime
import time, undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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

write_filename = "final_kidsfootlocker_" + date_now + ".csv"
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

urls = []

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		# 'proxy_country': 'us',
		'js_render': 'true',
	}
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def extract_state_from_server(raw: str) -> dict:
	# 1) Find start of STATE_FROM_SERVER and its opening brace
	i = raw.find('STATE_FROM_SERVER')
	if i == -1:
		raise ValueError("STATE_FROM_SERVER not found")
	j = raw.find('{', i)
	if j == -1:
		raise ValueError("Opening brace for STATE_FROM_SERVER not found")

	# 2) Balanced-brace extraction (handles strings/escapes)
	depth, k, in_str, esc, quote = 0, j, False, False, ""
	while k < len(raw):
		ch = raw[k]
		if in_str:
			if esc:
				esc = False
			elif ch == '\\':
				esc = True
			elif ch == quote:
				in_str = False
		else:
			if ch in ('"', "'"):
				in_str, quote = True, ch
			elif ch == '{':
				depth += 1
			elif ch == '}':
				depth -= 1
				if depth == 0:
					k += 1
					break
		k += 1
	if depth != 0:
		raise ValueError("Unbalanced braces in STATE_FROM_SERVER block")

	obj_txt = raw[j:k]

	# 3) Clean up JSON: remove trailing commas before } or ]
	obj_txt = re.sub(r',\s*([}\]])', r'\1', obj_txt)

	# 4) Parse to Python dict (keys/values in your snippet are already JSON-compatible)
	return json.loads(obj_txt)

def get_product_links():
	global urls
	# URL = "https://www.kidsfootlocker.com/en/category/sale.html"
	URL = 'https://www.kidsfootlocker.com/category/sale/flx'

	driver = uc.Chrome(headless=False); driver.set_window_size(1365, 900)
	w = W(driver, 15)
	driver.get(URL)

	# accept ToU/cookies if present
	try: w.until(EC.element_to_be_clickable((By.ID, "touAgreeBtn"))).click()
	except: pass

	seen = set()

	def print_links():
		cards = w.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-container")))
		for c in cards:
			try:
				href = c.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
				if href and href not in seen:
					seen.add(href)
					urls.append(href)
			except NoSuchElementException:
				continue

	def next_disabled():
		try:
			nxt = driver.find_element(By.CSS_SELECTOR, ".Pagination-option--next")
			a = nxt.find_element(By.TAG_NAME, "a")
		except NoSuchElementException:
			return True
		cls = ((a.get_attribute("class") or "") + " " + (nxt.get_attribute("class") or "")).lower()
		if "disabled" in cls or "is-disabled" in cls: return True
		if (a.get_attribute("aria-disabled") or "").lower() in ("true", "1"): return True
		if not (a.get_attribute("href") or "").strip(): return True
		return False

	c = 1
	while True:
		print(f"Scraping page {c}", end="\r")

		while True:
			try:
				print_links()
				break
			except Exception:
				driver.execute_cdp_cmd("Network.clearBrowserCache", {})
				driver.get(driver.current_url)
				continue

		if next_disabled(): break
		# click next and wait for content change
		sentinel = driver.find_elements(By.CSS_SELECTOR, ".product-container")
		sentinel = sentinel[0] if sentinel else None
		a = driver.find_element(By.CSS_SELECTOR, ".Pagination-option--next a")
		driver.execute_script("arguments[0].scrollIntoView({block:'center'});", a)
		try: a.click()
		except Exception: driver.execute_script("arguments[0].click()", a)
		if sentinel:
			try: W(driver, 10).until(EC.staleness_of(sentinel))
			except TimeoutException: time.sleep(1.5)
		else:
			time.sleep(1.5)

		c += 1

	driver.quit()

def get_product_info(link):
	while True:
		try:
			html = get_zenrows_html(link)
			soup = BeautifulSoup(html, 'html.parser')
			soup.find_all('script')
			break
		except Exception as e:
			print('Trying again...')

	for script in soup.find_all('script'):
		if script.get_text().strip().startswith('window.footlocker = {'):
			data_json = extract_state_from_server(script.get_text().strip())

			for var in data_json['api']['productDetails']['getDetails']['data']['styleVariants']:
				upc = var['upc']
				price = var['price']['salePrice']
				color = var['color'].replace('u002F', '')

				with counter_lock:
					with open(write_csv, 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([upc, price, color, link])

			break

if __name__ == "__main__":
	get_product_links()

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')