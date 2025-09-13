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
    }
    response = requests.get(zenrows_url, params=params, timeout=120)
    response.raise_for_status()
    return response.text

# --- Read all URLs from product_url.csv ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_csv_file = os.path.join(script_dir, 'product_url.csv')
output_csv_file = os.path.join(script_dir, 'final_nike.csv')

product_urls = []
with open(input_csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader, None)
    for row in reader:
        product_urls.append(row[0])

if os.path.exists(output_csv_file):
    os.remove(output_csv_file)
    print(f"Deleted existing file: {output_csv_file}")

header = ['upc', 'price', 'variation', 'promotion', 'source_url']
csv_lock = threading.Lock()
counter_lock = threading.Lock()
counter = [0]

def process_url(args):
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
                data = json.loads(script_tag.get_text())
                groups = data['props']['pageProps']['productGroups']
                for item in groups:
                    groupLabel = item['groupLabel'] + ' - ' if item['groupLabel'] else ''
                    for it in item['products'].keys():
                        source_url = str(item['products'][it]['pdpUrl']['url'])
                        price = item['products'][it]['prices']['currentPrice']
                        color = item['products'][it]['colorDescription']
                        for get_upc in item['products'][it]['sizes']:
                            upc = '\'' + str(get_upc['gtins'][0]['gtin'])[2:]
                            variation = groupLabel + color + ' - ' + get_upc['label']
                            results.append([upc, price, variation, 'EXTRA 20% Off with code SPORT', source_url])
            break  # Only break if successful
        except Exception as e:
            attempts += 1
            if attempts >= max_retries:
                print(f"Failed after {max_retries} attempts: {url}")
            time.sleep(2)  # Pause before retry

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

if __name__ == "__main__":
    # Write header row once at the start
    with open(output_csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    total_urls = len(product_urls)
    arglist = [(url, idx + 1, total_urls) for idx, url in enumerate(product_urls)]

    with ThreadPoolExecutor(max_workers=20) as executor:
        list(executor.map(process_url, arglist))

    print("All done.")
