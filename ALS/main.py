from playwright.sync_api import sync_playwright
import re
import os
from datetime import datetime
from pathlib import Path
import csv
from dotenv import load_dotenv
import math
import random
import time

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")
zenrows_api = 'https://api.zenrows.com/v1/'
############################## ZENROWS ##################################

write_filename = "product_urls_als_" + date_now + ".csv"
write_headers = ['URLs']
############################# CSV WRITE #################################
script_dir = os.path.dirname(os.path.abspath(__file__))
write_csv = os.path.join(script_dir, write_filename)
if os.path.exists(write_csv):
	os.remove(write_csv)
	print(f"Deleted existing file: {write_csv}\nStarting now...\n")

with open(write_csv, 'w', newline='', encoding='utf-8') as f:
	writer = csv.writer(f)
	writer.writerow(write_headers)
############################# CSV WRITE #################################

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)
page = browser.new_page()

def get_total_products(url):
	page.goto(url, timeout=120_000)
	page.wait_for_selector(f'li[id="li-next-button"]', timeout=30_000)
	p_elements = page.locator('li[id="li-next-button"]').all_inner_texts()
	total_products = int(re.findall(r'\d+', p_elements[0])[0])

	li_selector = 'div#gallery-container ul li.flex-1:not(.hidden)'
	visible_li_locator = page.locator(li_selector)
	visible_li_count = visible_li_locator.count()

	return total_products+visible_li_count

def get_product_links(page_no, url):
	url = f'{url}?page={page_no}'
	page.goto(url, timeout=120_000)
	page.wait_for_selector('div#gallery-container', timeout=30_000)
	
	hrefs = []
	li_locators = page.locator('div#gallery-container li')
	for i in range(li_locators.count()):
		li = li_locators.nth(i)
		a_tag = li.locator('a')
		if a_tag.count() > 0:
			href = a_tag.first.get_attribute('href')
			if href:
				# Remove query string for uniqueness
				base_href = href.split('?')[0]
				hrefs.append(base_href)
	# Remove duplicates while preserving order
	unique_hrefs = list(dict.fromkeys(hrefs))
	for href in unique_hrefs:
		with open(write_csv, 'a', newline='', encoding='utf-8') as f:
			writer = csv.writer(f)
			writer.writerow([f'https://www.als.com'+href])

if __name__ == "__main__":
	# url = 'https://www.als.com/nike'
	# url = 'https://www.als.com/kids--clothing---footwear'
	# url = 'https://www.als.com/back-to-school-packs?map=productclusternames'
	# url = 'https://www.als.com/promotions/labor-day-sale'
	url = 'https://www.als.com/promotions/summer-clearance-2025'
	total_products = get_total_products(url)
	total_pages = math.ceil(int(total_products)/32)
	print(f'Found {total_pages} pages')

	for i in range(1, total_pages + 1):
		print(f'Processing page {i} / {total_pages}')
		get_product_links(i, url)
		time.sleep(random.uniform(1.5, 4.0))

	p.stop()

	print('\nDone.')
