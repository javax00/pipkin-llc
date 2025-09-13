import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import time
import threading
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))
############################## ZENROWS ##################################
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")
zenrows_api = 'https://api.zenrows.com/v1/'
############################## ZENROWS ##################################

write_filename = "ck_product_urls_" + date_now + ".csv"
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

lock = threading.Lock()
counter = {
    'done': 0,
    'total': 0
}

def get_zenrows_html(target_url):
    params = {
        'apikey': ZENROWS_API_KEY,
        'url': target_url,
        'premium_proxy': 'true',
        'js_render': 'true',
        'proxy_country': 'us',
        'wait': '5000'
    }
    # r = requests.get(zenrows_api, params=params, timeout=60)
    r = requests.get(target_url, timeout=60)
    time.sleep(10)  # reduce delay when using threads
    return r.text

def get_total_products(url, count):
    html_content = get_zenrows_html(url)
    soup = BeautifulSoup(html_content, 'html.parser')
    products = soup.find_all("div", class_="productTileShow")

    rows = []
    for product in products:
        product_url = product.find("a", class_="ds-product-name")
        if product_url:
            full_url = 'https://www.calvinklein.us' + product_url.get("href", "")
            rows.append([full_url])
    
    with lock:
        with open(write_csv, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        counter['done'] += 1
        print(f"Thread done: {counter['done']}/{counter['total']}")

if __name__ == "__main__":
    url = 'https://www.calvinklein.us/en/sale'
    # url = 'https://www.calvinklein.us/en/sale/featured/new-to-sale'
    # url = 'https://www.calvinklein.us/en/summer-sale/women?ab=bb.1_w-lastChance-250812'
    html = get_zenrows_html(url)
    soup = BeautifulSoup(html, "html.parser")

    search_result_count = soup.find('span', class_='search-result-count').text
    count = int(''.join(filter(str.isdigit, search_result_count)))
    print(f"Total products found: {count}")

    start = 0
    urls = []
    while start < count:
        urls.append(f'{url}&sz=16&start={start}')
        start += 16

    counter['total'] = len(urls)

    threads = []
    max_threads = 50

    def thread_worker(url):
        get_total_products(url, count)

    for url in urls:
        while threading.active_count() > max_threads:
            time.sleep(0.1)
        t = threading.Thread(target=thread_worker, args=(url,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print("Scraping completed.")
