import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import time
import threading
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")
zenrows_api = 'https://api.zenrows.com/v1/'
############################## ZENROWS ##################################

write_filename = "product_urls_michaels_" + date_now + ".csv"
write_headers = ['URLs']
############################# CSV WRITE #################################
script_dir = os.path.dirname(os.path.abspath(__file__))
write_csv = os.path.join(script_dir, write_filename)
if os.path.exists(write_csv):
	os.remove(write_csv)
	print(f"Deleted existing file: {write_csv}...")

with open(write_csv, 'w', newline='', encoding='utf-8') as f:
	writer = csv.writer(f)
	writer.writerow(write_headers)
############################# CSV WRITE #################################


# FINAL LINK CSV
final_write_filename = "final_product_urls_michaels_" + date_now + ".csv"
final_write_headers = ['API URLs', 'Original URLs']
############################# CSV WRITE #################################
final_script_dir = os.path.dirname(os.path.abspath(__file__))
final_write_csv = os.path.join(final_script_dir, final_write_filename)
if os.path.exists(final_write_csv):
	os.remove(final_write_csv)
	print(f"Deleted existing file: {final_write_csv}\nStarting now...\n")

with open(final_write_csv, 'w', newline='', encoding='utf-8') as f:
	writer = csv.writer(f)
	writer.writerow(final_write_headers)
############################# CSV WRITE #################################

def get_zenrows_html(target_url, wait):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'js_render': 'true',
		'proxy_country': 'us',
		'wait_for': wait
	}
	r = requests.get(zenrows_api, params=params, timeout=120)
	return r.text

def get_product_urls(page_no):
    url = 'https://www.michaels.com/ia/art-supplies/fine-art-markers-pen-pencil-sets?page='+str(page_no)
    html = get_zenrows_html(url, 'nav#pagination')
    soup = BeautifulSoup(html, "html.parser")
    
    con = soup.find('div', class_='css-8el0kn').find_all('div', class_='css-79elbk')
    for item in con:
        link = 'https://www.michaels.com'+item.find('a', class_='styles_product-styled-link__lFcoC').get('href')
        
        with open(write_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([link])

def get_product_api(product_url):
    html = get_zenrows_html(product_url, 'div.css-ljjwvb')
    soup = BeautifulSoup(html, "html.parser")

    data_json = soup.find_all('script', type='application/ld+json')[-1].get_text()
    data_json = json.loads(data_json)

    base = data_json['url'].split('-')[-1]

    if data_json['isRelatedTo']['url'] != []:
        sku_numbers = []
        for sku in data_json['isRelatedTo']['url']:
            sku_numbers.append(sku.split('-')[-1])
        sku_number = ','.join(sku_numbers)
    else:
        sku_number = base

    final_url = f'https://www.michaels.com/api/product/v2/sub-skus?source=pdpPage&orginSkuNumber={base}&michaelsStoreId=9055&isNewUIMkpMik=false&skuNumbers={sku_number}'
    
    with open(final_write_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([final_url, product_url])

if __name__ == '__main__':
    url = 'https://www.michaels.com/ia/art-supplies/fine-art-markers-pen-pencil-sets'
    html = get_zenrows_html(url, 'nav#pagination')
    soup = BeautifulSoup(html, "html.parser")

    pages = int(soup.find('nav', id='pagination').text.strip().split('…')[-1])
    print(f'Found {pages} pages')

    counter = 0
    counter_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(get_product_urls, page_no): page_no for page_no in range(1, pages+1)}
        for future in as_completed(futures):
            with counter_lock:
                counter += 1
                print(f"Getting product urls page {counter} / {pages}", end='\r')

    print("\nSaved product urls\n\nGetting API urls...")
    time.sleep(5)

    read_filename = "product_urls_michaels_" + date_now + ".csv"
    ############################# CSV READ ##################################
    script_dir = os.path.dirname(os.path.abspath(__file__))
    read_csv = os.path.join(script_dir, read_filename)

    product_urls = []
    with open(read_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            product_urls.append(row)
    ############################# CSV READ ##################################

    # for product_url in product_urls:
    #     get_product_api(product_url[0])

    counter = 0
    counter_lock = threading.Lock()

    total = len(product_urls)
    print(f'Scraping {total} product urls')

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(get_product_api, url[0]) for url in product_urls]
        for future in as_completed(futures):
            with counter_lock:
                counter += 1
                print(f"Getting final url {counter} / {total}", end='\r')

    print("\n\nDone")
