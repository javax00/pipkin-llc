import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import requests
import random
from concurrent.futures import ThreadPoolExecutor, as_completed 
import os
import csv
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get ZenRows API key from environment variables
zenrows_api_key = os.getenv('ZENROWS_API_KEY')
if not zenrows_api_key:
    raise ValueError("Please set ZENROWS_API_KEY in your .env file")

# URL = "https://www.vincecamuto.com/collections/buy-more-save-more-event"
# URL = "https://www.vincecamuto.com/collections/30-off-select-styles"
# URL = "https://www.vincecamuto.com/collections/25-off-select-styles"
URL = 'https://www.vincecamuto.com/collections/50-off-sandal-promotion'

zenrows_url = "https://api.zenrows.com/v1/"

def fetch_barcodes(target_url):
    while True:
        json_url = target_url.rstrip("/") + ".json"
        params = {
            'url': json_url,
            'apikey': zenrows_api_key,
            'premium_proxy': 'true',
            'proxy_country': 'us',
        }
        results = []
        try:
            r = requests.get(zenrows_url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            for variant in data['product']['variants']:
                barcode = variant['barcode']
                price = float(variant['price'])*.70
                variant = variant['title']
                results.append((barcode, price, variant, target_url))
            return results
        except Exception as e:
            print("Trying again...")

async def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    date_now = str(datetime.now().strftime("%m_%d_%Y"))
    save_vincecamuto_final = os.path.join(script_dir, f'vincecamuto_final_{date_now}.csv')

    # Delete file if exists
    if os.path.exists(save_vincecamuto_final):
        os.remove(save_vincecamuto_final)
        print(f"Deleted existing file: {save_vincecamuto_final}")
    else:
        print(f"No existing file found. Creating a new one.")

    # Create header and save all results
    with open(save_vincecamuto_final, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['UPC', 'Price', 'Variation', 'Source Link'])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(URL)
        await asyncio.sleep(3)

        unchanged_count = 0
        last_height = await page.evaluate("() => document.body.scrollHeight")

        while unchanged_count < 3:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            new_height = await page.evaluate("() => document.body.scrollHeight")

            if new_height == last_height:
                unchanged_count += 1
            else:
                unchanged_count = 0
                last_height = new_height

        html = await page.content()
        await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        products = soup.find_all('div', class_='product-grid-item__container')

        valid_links = []
        for product in products:
            a_tag = product.find('a', href=True)
            if a_tag:
                href = a_tag['href']
                if href.startswith('/'):
                    href = "https://www.vincecamuto.com" + href
                valid_links.append(href)

        print('total products:', len(valid_links))

        # =====================
        # BARCODE THREADS WITH WORKERS
        # =====================
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(fetch_barcodes, href) for href in valid_links]
            for future in as_completed(futures):
                results = future.result()
                for barcode, price, variant, url in results:

                    # Save all results to file
                    with open(save_vincecamuto_final, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow([barcode, price, variant, url])
                    # =====================

    print('Done')

# Run the script
asyncio.run(main())
