from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
import math
from datetime import datetime
import os
import csv
import random
import time

date_now = str(datetime.now().strftime("%m_%d_%Y"))
write_filename = "product_urls_revolve_" + date_now + ".csv"
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

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)
context = browser.new_context()
page = context.new_page()

def scrape_revolve(url):
	page.goto(url, timeout=60000, wait_until="domcontentloaded")
	page.wait_for_selector('ul#plp-prod-list li.plp__product')

	try:
		page.click('a#ntf_dialog_close', timeout=2000)
	except Exception:
		pass

	html = page.content()
	return html

if __name__ == '__main__':
	# url = 'https://www.revolve.com/sale/all-sale-items/br/54cc7b/'
	url = 'https://www.revolve.com/beauty/br/114440/'
	html = scrape_revolve(url)
	soup = BeautifulSoup(html, 'html.parser')
	total_page = math.ceil(int(soup.find('span', class_='js-item-count').text.replace(',', ''))/500)
	print(f'Found {total_page} pages')

	for i in range(1, total_page + 1):
		print(f'Scraping page {i} / {total_page}', end='\r')
		html = scrape_revolve(f'{url}?pageNum={i}')
		soup = BeautifulSoup(html, 'html.parser')
		products = soup.find('ul', id='plp-prod-list').find_all('li', class_='plp__product')
		for c, product in enumerate(products, 1):
			link = product.find('a', class_='plp__image-link')
			if link and link.get('href'):
				with open(write_csv, 'a', newline='', encoding='utf-8') as f:
					writer = csv.writer(f)
					writer.writerow([f"https://www.revolve.com{link.get('href')}"])
		time.sleep(random.randint(2, 5))

	browser.close()
	p.stop()

	print('Done')
