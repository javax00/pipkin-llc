import requests
import time
from dotenv import load_dotenv
from pathlib import Path
import os
from bs4 import BeautifulSoup
import json
import csv
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))
# Load ZenRows API key
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
zenrows_api_key = os.getenv('ZENROWS_API_KEY')
if not zenrows_api_key:
	raise ValueError("Please set ZENROWS_API_KEY in your .env file")

zenrows_url = "https://api.zenrows.com/v1/"

# Load all product URLs from CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'product_url_' + date_now + '.csv')
if not os.path.exists(csv_file):
	raise FileNotFoundError(f"CSV file not found: {csv_file}")

product_urls = []
with open(csv_file, newline='', encoding='utf-8') as f:
	reader = csv.DictReader(f)
	for row in reader:
		product_urls.append(row['Product URL'])

# product_urls = ['https://www.famousfootwear.com/product/adidas-kids-kaptir-3-0-sneaker-little-big-kid-1054515',
# 				'https://www.famousfootwear.com/product/puma-mens-court-ultra-sneaker-5273095']

# product_urls = ['https://www.famousfootwear.com/product/adidas-kids-barreda-decode-sneaker-big-kid-1058258',
# 				'https://www.famousfootwear.com/product/adidas-kids-barreda-decode-sneaker-little-kid-1059265']

print(f"Loaded {len(product_urls)} product URLs.")

# Output file path
output_file = os.path.join(script_dir, 'final_famousfootwear_' + date_now + '.csv')

# Remove the file if it exists
if os.path.exists(output_file):
	os.remove(output_file)
	print(f"Deleted existing file: {output_file}\n")
else:
	print(f"No existing file found. Creating a new one.\n")

# Open CSV file for writing results (header row)
with open(output_file, mode='w', newline='', encoding='utf-8') as file:
	writer = csv.writer(file)
	writer.writerow(['UPC', 'Price', 'Variation', 'Source Link'])

# Function to fetch UPCs and write data to CSV for each product URL
def process_product_url(product_url, index, total):
	valid_upc_count = 0  # Counter for valid UPCs per product URL
	
	print(f"Processing {index + 1}/{total}")
	params = {
		'url': product_url,
		'apikey': zenrows_api_key,
		'premium_proxy': 'true',
		'proxy_country': 'ca',
		'js_render': 'true',
		'antibot': 'true',
		'wait_for': '#productDetailData'
	}

	try:
		r = requests.get(zenrows_url, params=params, timeout=60)
		soup = BeautifulSoup(r.text, "html.parser")
		all_data = soup.find("div", id="productDetailData")
		
		if all_data:
			data = json.loads(all_data.get("data-product-detail-data"))
			for details in data['ProductGroupItems']:
				source_link = 'https://www.famousfootwear.com'+details['Uri']
				price = details['AdjustedPriceNumeric']
				variation = details['Color']
				
				# Fetch UPC from UPCitemdb API
				upc_url = f"https://api.upcitemdb.com/prod/trial/search?s={details['VendorSku']}"
				proxy_country = random.choice(['gb', 'ca', 'de', 'fr', 'it', 'es', 'nl', 'au', 'jp', 'sg', 'br', 'in'])
				upc_params = {
					'url': upc_url,
					'apikey': zenrows_api_key,
					'premium_proxy': 'true',
					'proxy_country': proxy_country,
				}

				try:
					r_upc = requests.get(zenrows_url, params=upc_params, timeout=30)
					data_upc = r_upc.json()

					# Check for "NOT_FOUND" response
					if isinstance(data_upc, dict) and data_upc.get("code") == "NOT_FOUND":
						upc = 'Not Found'
					else:
						# Extract the first UPC if found
						items = data_upc.get("items", [])
						if items:
							for item in items:
								upc = item.get('ean', '')[1:]  # Adding the ' in front of UPC
								if upc:  # Only write if UPC is found
									valid_upc_count += 1  # Increment the valid UPC count
									with open(output_file, mode='a', newline='', encoding='utf-8') as file:
										writer = csv.writer(file)
										writer.writerow([upc, price, variation, source_link])

				except Exception as e:
					print(f"Error fetching UPC for VendorSku {details['VendorSku']}: {e}")

				time.sleep(2)  # Small delay between requests

		else:
			print("❌ Could not find #productDetailData")

	except Exception as e:
		print(f"❌ Error fetching page: {e}")
		return 0  # Return 0 if there was an error with the product URL
	
	return valid_upc_count

# Using ThreadPoolExecutor with 50 workers
with ThreadPoolExecutor(max_workers=50) as executor:
	futures = []
	for index, url in enumerate(product_urls):
		futures.append(executor.submit(process_product_url, url, index, len(product_urls)))

	# Process results as they complete
	for future in as_completed(futures):
		valid_upc_count = future.result()

print('Done')
