import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import concurrent.futures
import requests
import os
import json
from dotenv import load_dotenv
from pathlib import Path
import time
import re
import html
import json as pyjson  # To avoid conflict with 'json' import
import csv

product_links = []
async def main():
    url = "https://www.healthydirections.com/product-categories/catalog-limited-offer"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, timeout=120_000)
        
        input("Solve any Cloudflare captcha in the browser.\nPress Enter here when you're done:")

        # Try to close the ad/modal if it appears
        try:
            await page.wait_for_selector("button.bx-close-inside", timeout=5000)
            await page.click("button.bx-close-inside")
            print("Closed the ad/modal.")
        except Exception:
            print("Ad/modal close button not found (skipping).")

        for i in range(100):  # Set a high limit for safety
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await page.wait_for_timeout(1000)
            # Scroll to top
            await page.evaluate("window.scrollTo(0, 0);")
            await page.wait_for_timeout(1000)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            product_container = soup.find("div", id="productContainer")

            print("Scrolling to load more")

            if "End of Search Results" in soup.find("body").get_text():
                break

        # Final scrape after all products are loaded
        if not product_container:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            product_container = soup.find("div", id="productContainer")

        if product_container:
            product_divs = product_container.find_all("div", class_="p-2")
            for idx, div in enumerate(product_divs, 1):
                a_tag = div.find('a')
                if a_tag:
                    link = a_tag.get('href')
                    product_links.append(link)
        else:
            print("No div with id='productContainer' found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())


# ===== ZENROWS SECTION BELOW =====

# CSV setup
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'final_healthydirections.csv')
if os.path.exists(csv_file):
    os.remove(csv_file)
    print(f"Deleted existing file: {csv_file}\nStarting now...\n")

# CSV header
header = ['UPC', 'Price', 'Promo', 'Link']
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(header)

def clean_json_string(raw):
    # 1. Unescape HTML entities (&quot;, &amp;, etc.)
    cleaned = html.unescape(raw)

    # 2. Remove trailing commas before } or ]
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)

    # 3. Replace unescaped control characters (like newlines, tabs) inside strings
    # This pattern finds all "..." string values and replaces internal newlines/tabs with a space
    def fix_control_chars(match):
        content = match.group(0)
        # Only process if inside quotes
        return re.sub(r'[\r\n\t]', ' ', content)
    cleaned = re.sub(r'"(.*?)"', fix_control_chars, cleaned, flags=re.DOTALL)

    # 4. Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    return cleaned

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
ZENROWS_API_KEY = os.getenv('ZENROWS_API_KEY')
zenrows_url = "https://api.zenrows.com/v1/"

def fetch_with_zenrows(link):
	params = {
		"url": link,
		"apikey": ZENROWS_API_KEY,
		"js_render": "true",
		"premium_proxy": "true",
		"proxy_country": "us",
		"wait": "2000"
	}
	upc, price, promo, source_url = '', '', '', ''
	try:
		r = requests.get(zenrows_url, params=params, timeout=60)
		if r.status_code == 200:
			soup = BeautifulSoup(r.text, "html.parser")
			found = False
			for script in soup.find_all("script", type="application/ld+json"):
				try:
					raw_json = script.string
					cleaned_json = clean_json_string(raw_json)
					data = pyjson.loads(cleaned_json)
					upc = '\''+data['sku']
					source_url = data['@id']
					# === Find the button in div#pricing_container as requested ===
					pricing_container = soup.find("div", id="pricing_container")
					if pricing_container:
						# Find all buttons under this div (descendants)
						buttons = pricing_container.find_all("button")
						selected_button = None
						priority_texts = ["Best Value", "Most Popular"]

						for priority in priority_texts:
							for btn in buttons:
								if btn.get_text(strip=True).lower().find(priority.lower()) != -1:
									selected_button = btn
									break
							if selected_button:
								break

						# If not found, pick the first button
						if not selected_button and buttons:
							selected_button = buttons[0]

						if selected_button:
							btn_text = selected_button.get_text(" ", strip=True)
							promo = btn_text.split('Retail')[0].strip()

							# --- Extract all prices ---
							prices = re.findall(r'\$\s*([0-9]+(?:[.,][0-9]{2})?)', btn_text)
							prices_float = [float(p.replace(',', '')) for p in prices]
							if prices_float:
								cheapest = min(prices_float)
								price = cheapest

							with open(csv_file, 'a', newline='', encoding='utf-8') as f:
								writer = csv.writer(f)
								writer.writerow([upc, price, promo, source_url])

					found = True
				except Exception as e:
					pass
		return r.text

	except Exception as e:
		print(f"Error fetching {link}: {e}")
		return None

# product_links = product_links[:1]

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
	future_to_link = {executor.submit(fetch_with_zenrows, link): link for link in product_links}
	for i, future in enumerate(concurrent.futures.as_completed(future_to_link), 1):
		# link = future_to_link[future]
		# try:
		# 	data = future.result()
		# 	results.append((link, data))
		# except Exception as exc:
		# 	print(f"{link} generated an exception: {exc}")
		print(f"Progress: {i}/{len(product_links)}")

print("Done")