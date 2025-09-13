import requests
import os
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
import json
import csv
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))

# === Load ZenRows API Key from .env ===
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
if not ZENROWS_API_KEY:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")

def zenrows_request(target_url):
    zenrows_url = "https://api.zenrows.com/v1/"
    params = {
        'apikey': ZENROWS_API_KEY,
        'url': target_url,
        'js_render': 'true',
        'premium_proxy': 'true',
        'proxy_country': 'US',
        # 'wait_for': 'script#__NEXT_DATA__',
        'wait': '20000'
    }
    # response = requests.get(zenrows_url, params=params, timeout=90)
    response = requests.get(target_url, timeout=90)
    response.raise_for_status()
    return response.text

# --- Read all URLs from product_url.csv ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_csv_file = os.path.join(script_dir, 'puma_product_urls_' + date_now + '.csv')
output_csv_file = os.path.join(script_dir, 'final_puma_' + date_now + '.csv')

product_urls = []
with open(input_csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader, None)
    for row in reader:
        product_urls.append(row[0])

# product_urls = product_urls[:1]

if os.path.exists(output_csv_file):
    os.remove(output_csv_file)
    print(f"Deleted existing file: {output_csv_file}\n")

header = ['upc', 'price', 'variation', 'source_url']
csv_lock = threading.Lock()
counter_lock = threading.Lock()
counter = [0]

def process_url(args):
    try:
        url, idx, total = args
        results = []
        max_retries = 5
        attempts = 0
        while attempts < max_retries:
            try:
                html = zenrows_request(url)
                soup = BeautifulSoup(html, 'html.parser')
                script_tag = soup.find('script', id='__NEXT_DATA__', type='application/json')
                if script_tag:
                    break
            except Exception as e:
                print(str(e))
                attempts += 1
                if attempts >= max_retries:
                    print(f"Failed after {max_retries} attempts: {url}")



        data = json.loads(script_tag.get_text())
        groups = data['props']['urqlState']

        for group in groups:
            try:
                json_data = json.loads(groups[group]['data'])['product']
                if json_data['id'] == url.split('/')[-1]:
                    for v in json_data['variations']:
                        upc = v['variantId']
                        price = v['salePrice']
                        variation = v['colorName']
                        source_url = url+'?swatch='+v['colorValue']

                        results.append([upc, price, variation, source_url])
                    break
            except Exception as e:
                continue


        # Save immediately after processing each link
        if results:
            with csv_lock:
                with open(output_csv_file, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(results)

        # Print counter after saving
        with counter_lock:
            counter[0] += 1
            print(f"Processed {counter[0]}/{total} links")
    except Exception:
        pass

if __name__ == "__main__":
    # Write header row once at the start
    with open(output_csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    total_urls = len(product_urls)
    arglist = [(url, idx + 1, total_urls) for idx, url in enumerate(product_urls)]

    with ThreadPoolExecutor(max_workers=50) as executor:
        list(executor.map(process_url, arglist))

    print("\nAll done.")
