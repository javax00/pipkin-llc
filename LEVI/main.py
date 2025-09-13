import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
from datetime import datetime
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

write_filename = "final_levi_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variation', 'Source Link']
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
all_code = []

def get_zenrows_html(target_url, wait):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
		'wait_for': wait,
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_links(page):
	global urls
	if page == 0:
		url = 'https://www.levi.com/US/en_US/levis-select-styles-promos/levis-select-styles-promos-for-women/c/levi_clothing_select_styles_promos_women_us'
	else:
		url = f'https://www.levi.com/US/en_US/levis-select-styles-promos/levis-select-styles-promos-for-women/c/levi_clothing_select_styles_promos_women_us?page={page}'
	html = get_zenrows_html(url, 'div.results-grid')
	soup = BeautifulSoup(html, 'html.parser')
	
	for link in soup.find_all('div', class_='results-grid')[0].find_all('div', class_='product-cell'):
		with counter_lock:
			urls.append('https://www.levi.com'+link.find('a', class_='product-link').get('href'))

def get_product_code(link):
	global all_code
	html = get_zenrows_html(link, 'li.swatch-wrapper')
	soup = BeautifulSoup(html, 'html.parser')

	for code in soup.find_all('li', class_='swatch-wrapper'):
		with counter_lock:
			all_code.append(code.get('code'))

def get_product_info(code):
	params = {
		"apikey": ZENROWS_API_KEY,
		"url": "https://www.levi.com/nextgen-webhooks/?operationName=product&locale=US-en_US",
		"custom_headers": "true",
		"premium_proxy": "true",
		"proxy_country": "us",
	}

	payload = json.dumps({
		"operationName": "product",
		"variables": {"code": code},
		"query": "query product($code: String!) {\n  product(code: $code) {\n    altText\n    averageOverallRatings\n    backOrder\n    baseProduct\n    bopisAvailable\n    channels\n    classifications {\n      code\n      features {\n        code\n        featureValues {\n          value\n          code\n        }\n        name\n        range\n        type\n      }\n      name\n    }\n    code\n    colorName\n    comingSoon\n    crossSellProductUrl\n    crossSellSizeGroup\n    customizable\n    flxCustomization\n    department\n    productSizeCoverage\n    pdpGroupId\n    preOrder\n    preOrderShipDate\n    returnable\n    description\n    findInStoreEligible\n    lowestRecentPriceData {\n      currencyIso\n      formattedValue\n      value\n    }\n    discountPCT\n    lscoBreadcrumbs {\n      categoryCode\n      name\n      url\n    }\n    galleryImageList {\n      galleryImage {\n        altText\n        format\n        galleryIndex\n        imageType\n        modelDescription\n        url\n      }\n      videos {\n        altText\n        format\n        galleryIndex\n        modelDescription\n        url\n      }\n    }\n    itemType\n    maxOrderQuantity\n    merchantBadge\n    minOrderQuantity\n    name\n    noOfRatings\n    pdpCmsContentId1\n    pdpCmsContentId2\n    preferredCategory\n    price {\n      code\n      currencyIso\n      formattedValue\n      hardPrice\n      hardPriceFormattedValue\n      maxQuantity\n      minQuantity\n      priceType\n      regularPrice\n      regularPriceFormattedValue\n      softPrice\n      softPriceFormattedValue\n      value\n    }\n    productSchemaOrgMarkup {\n      brand {\n        entry {\n          key\n          value\n        }\n      }\n      gtin12\n      offers {\n        entry {\n          key\n          value\n        }\n      }\n    }\n    promotionalBadge\n    redirectUrl\n    seoMetaData {\n      metaDescription\n      metaH1\n      metaTitle\n      robots\n    }\n    sizeGuide\n    soldIndividually\n    soldOutForever\n    url\n    variantLength\n    variantOptions {\n      code\n      colorName\n      displaySizeDescription\n      maxOrderQuantity\n      minOrderQuantity\n      priceData {\n        code\n        currencyIso\n        formattedValue\n        hardPrice\n        hardPriceFormattedValue\n        maxQuantity\n        minQuantity\n        priceType\n        regularPrice\n        regularPriceFormattedValue\n        softPrice\n        softPriceFormattedValue\n        value\n      }\n      stock {\n        asnDate\n        asnQty\n        stockLevel\n        stockLevelStatus\n      }\n      upc\n      url\n    }\n    variantSize\n    variantType\n    variantWaist\n    inventoryDepthStoresList\n    timeRetrievedFromAPI\n  }\n}\n"
	})

	headers = {
		'accept': '*/*, application/json',
		'accept-language': 'en-US,en;q=0.9',
		'apollographql-client-name': 'levi-frontend',
		'apollographql-client-version': '204.0.0',
		'content-type': 'application/json',
		'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjM3NjQ3MiIsImFwIjoiMTU4OTA3MTQ1OCIsImlkIjoiMzVmNjZlZjAwNmJhZGM0YyIsInRyIjoiMDViOWEwNjM2MWYzYjc4NWNjYTBhY2YzNDIxYzU3OGYiLCJ0aSI6MTc1NDY0NDQwMjAwNn19',
		'origin': 'https://www.levi.com',
		'priority': 'u=1, i',
		'referer': 'https://www.levi.com/US/en_US/clothing/women/shorts/80s-mom-womens-shorts/p/A46950003',
		'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'same-origin',
		'traceparent': '00-05b9a06361f3b785cca0acf3421c578f-35f66ef006badc4c-01',
		'tracestate': '376472^@nr=0-1-376472-1589071458-35f66ef006badc4c----1754644402006',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
		'x-brand': 'levi',
		'x-country': 'US',
		'x-locale': 'en_US',
		'x-log-requesttime': '2025-08-08T09:13:22.005Z',
		'x-ngs-uniqueid': '305e7743-fa72-4b18-a045-e633aa79f591--2d5bb919-3d54-4152-9ee7-261a7ec67540',
		'x-operationname': 'product',
		'x-selected-store': 'null',
		'x-sessionid': 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiIyOTc1NjllZS01YzBjLTRjNGUtOWJiNC04YzA0MWQwMTk4ZmQiLCJ1c2VySWQiOiJhbm9ueW1vdXMiLCJhY2Nlc3NUb2tlbiI6IiIsInJlZnJlc2hUb2tlbiI6IiIsImFjY2Vzc1Rva2VuRXhwaXJlcyI6IiIsImlzR3Vlc3QiOnRydWUsImxhc3RVcGRhdGVUaW1lIjoxNzU0NjQ0NDAwNDM1LCJsb2dpbk9iaiI6eyJsb2dnZWRJbiI6ZmFsc2UsImxvZ2luRXhwaXJhdGlvbiI6bnVsbCwiaGFzRXhwaXJlZCI6ZmFsc2V9LCJpYXQiOjE3NTQ2NDQ0MDAsImV4cCI6MTc1NDY0NjIwMCwiYXVkIjoiZ3JhcGhxbC51c2VyIiwiaXNzIjoibGV2aS53ZWJob29rcyIsInN1YiI6ImFwb2xsbyJ9.-nSug6LpBJ5BdGDJvXhsweoi8Fx2z3zfRRWZ9tNsETntT1hFTD0BUYCbg5s_WPSFTBfql1TS6ff69ccpgFY0ng',
		'Cookie': 'STATE=CA; LevisID=305e7743-fa72-4b18-a045-e633aa79f591; ajs_anonymous_id=305e7743-fa72-4b18-a045-e633aa79f591; lsco_kv=true; ConstructorioID_client_id=8ab2068e-41b5-4259-9788-519a1f665539; _gcl_au=1.1.784590295.1754634946; notice_behavior=implied,us; AMCVS_B7FF1CFE5330995F0A490D45%40AdobeOrg=1; pixlee_analytics_cookie=%7B%22CURRENT_PIXLEE_USER_ID%22%3A%22ba3c922f-b634-eef0-0be0-0d9a6468e642%22%7D; ajs_anonymous_id=305e7743-fa72-4b18-a045-e633aa79f591; lsa_fm=browse; s_cc=true; _ga=GA1.1.1523318072.1754634952; _scid=IRrHeB2WmWENDBHaaWxslTUvg_iiOI78; _tt_enable_cookie=1; _ttp=01K2469922E9K07XJ874J87WFT_.tt.1; _ScCbts=%5B%5D; QuantumMetricUserID=04f7601de7890821092924b17ca3bed8; _pin_unauth=dWlkPVlUTTJZVGswTjJNdE56RTBOUzAwTldGaExUazROR0V0WXpsbU1qSTFZVE5sTUdVMw; _sctr=1%7C1754582400000; bm_ss=ab8e18ef4e; ZIPCODE=94102; alb_origin=Levi_US_W_ng_green; bm_mi=8780E9E51339D53ED3253EDF9BB8AE79~YAAQS2DQFwxAdoaYAQAA/bbziByDoUjrNh0/D8OE93v/+Lh0LbYn6MOOSrW2rVH3X8uGQ+Khho99is1AZ9TUawcDw1LIL/lR9nYAWjZtXEEezKIPhO0NAXJOGFQV9xTUe9qh+8aQjJpedaTNoqptuGltwC92qJdz9wSNfOq1/gACLKZKOv7/9rxEDBGNSJ8rEQq0vnhLatsJ3Fml2qEDJXqxfy8/4K+jx3f+yJ7zo5OJBqV8NEahRfNvbvrzePYIJvCP/AA9KsCLBphX4l7GktzD31+MOZ0B4VU4BuOmCgtZxHiCwEhBwiPL/BfOAzJrsbDr4suegOOYQcYz9CQpbcZJBG7WcDikiqhnOujCsIEXVDLUuShfVtcX/PFpwcuoiKdFtxPgEzjTa4cvwj5xPWa0DYrcQyDUgQXfA+6ityakkY/mqLuFkNjejH/wzr6NpEIUmqXzTXJ+Hi56XQ==~1; bm_sc=4~1~615574717~YAAQS2DQFw5AdoaYAQAA/bbziAQ+Yz7qJ8U7S9hRjYAOF/77i5q1EI3tLR7A/4wcbqcpUvV5UdR8bhakig9uxDNXGauo7oKyUhjpdR1Xmik5YrJOJrNMDG+o7vW3/75VjjgR0EOCPf6vAuTo3c8eeZra9CMK2Tm8RX5sChLXfWQFib2Yl9MSwfsxjWt2ENLe9rBYyohbsTFlqmJPTFtlt7DjUmAkveF0ulm/BR7oBBJUO9JLa9kjt5IofUgWHKqfjkPc4YTmwWhM3J2OD8uYYuGYo7WEG1vt5GFZPOlRn2nj+Bk0A/nP8uQ4xEoAZaDKSRIv8xYU+E1Dk7G05Q+PioRU8qa39pI/m8ZU/grEDUtAE7qvQYUffElDLPmWSPtGxIpJyGMPqQMCdcVep0G/VGriY4grOIjVkKwkjNZ8XFtm+51269hs2titbJJQOF9siCUkfBZDHmbo8+pX8d07qMron9IhrlTMXNJGAZGRkkw/ft2zEJWHEwaHsudgBi5A0HDPLWF0m5Z2WsMJaLN7YhfACLo8DuudVGAVEiH94eV0Karf5tr7kb+i8wF7u+RM5i7gecQt/4tuyBnpULsYgImraDPmMbw=; bm_so=864832E898A80B341DED33A1AE2E0A8290C9D3B1DE355BEB35BE86D159E44969~YAAQS2DQF8nEdoaYAQAAjbT0iARkCywsW7RGQ3GxeMVBj0ioNuDrQTY4Cu77k8qATj8goZZlzrE54YnfhR5VeBUD1JB8tDzyyO0YV7dvx8nuXU9l5WwNBtDYJxc78nxJhk3irHbjosg64rWHLBJNWckIURRg5Qyl87bSHyjsKG0zFDtzk5WQ5SXESNNbS3/GMv21Osi8pjTRRyFNFWS8LFJMBY9SdClE/V2FSqn+FoEPvZ6VLDnSWlyq8VX+WACcXImx14o/aLJWLInfiYpWFMfhcY7kYwEHAqsh2ZaGxSeh0b3HTlPVNMM1So/safW8Q2+UgfCRkikM/ijMlw9BYcpjJSyKo1XbD4rTn+N0G8Kt++vez+0Yj2XOrv0cvPIrIjRg4OqgVYFD7E37ZYQ/6G/Ox0QbJLHW24ztqkLjKiVeq3FCe3v3AtLtpSv9EIEWWdU0Bi9asz9YuCyW; bm_lso=864832E898A80B341DED33A1AE2E0A8290C9D3B1DE355BEB35BE86D159E44969~YAAQS2DQF8nEdoaYAQAAjbT0iARkCywsW7RGQ3GxeMVBj0ioNuDrQTY4Cu77k8qATj8goZZlzrE54YnfhR5VeBUD1JB8tDzyyO0YV7dvx8nuXU9l5WwNBtDYJxc78nxJhk3irHbjosg64rWHLBJNWckIURRg5Qyl87bSHyjsKG0zFDtzk5WQ5SXESNNbS3/GMv21Osi8pjTRRyFNFWS8LFJMBY9SdClE/V2FSqn+FoEPvZ6VLDnSWlyq8VX+WACcXImx14o/aLJWLInfiYpWFMfhcY7kYwEHAqsh2ZaGxSeh0b3HTlPVNMM1So/safW8Q2+UgfCRkikM/ijMlw9BYcpjJSyKo1XbD4rTn+N0G8Kt++vez+0Yj2XOrv0cvPIrIjRg4OqgVYFD7E37ZYQ/6G/Ox0QbJLHW24ztqkLjKiVeq3FCe3v3AtLtpSv9EIEWWdU0Bi9asz9YuCyW^1754644397172; ConstructorioID_session={"sessionId":2,"lastTime":1754644398452}; _abck=D0696D8FDBD17EB45097E1A65B5B993E~-1~YAAQS2DQF0HPdoaYAQAAacn0iA5M0bLPPgPgylOoyPbKZ/t9J5hGkXAWW/fawIgcuQKjFCL+cGeQ59YIGGOkh3cq8CQlLBzwb4sIQDUQzh4eajWQ0Rxs4p4FhcotOJw39LpWmxvPs5atn8x4KWXl0vhcFakjZ1xJdbytZLUohHd5kVxGRSTI3URZiYASvzz0HnC2f9Xw1d/UtF6tdB+GeZ/dPIE5PUQ2MppWyzLumXz8URGm9zxN/wMQTYyGUYdlLVdPK0XdHdmTTLSLrp5ejE45GCtIYO6K2/R+5Om7PsfBmtVFL7NxEXJ/lrb6gfnVbVTk5X6T6FzGzSMFQCXDSqGHowpkdsIVuZXi6ewKrSWHWz24iQKxSTsRImj1zYzbZLc5K9dUPpunSPqZyD4gSLsTl6pC7QC8BzSDchnQQJEt6pFmex8ChAVj+Y/+PGIvi/Eiao3tzj2cBWMB6kzscdFqzNiXSJuL7Z/SUDpWCLrBZmaJCNnKOuZTxZX6Vru5q4UzqLSbWY81UtrpgkKgwQ2UmxmgyW6GfsYv2HiBLZA81WEEf6+MikvkJ0KGxFB70ot8ppzWMOzFOUBGHjkjyXdx2pCZgFeB2BsCVE82m9ZPcUf0SXoUTN1C+E0hR5VE5mNLXamm8YDMCMWZlTEFGLmdh9O+BC0fSfALS5k6aamVO7rl2OAHk9aqzeFJ8P+mgqBS1Dq7mvyxt4Qf2WnV8smBpK5dsxoJN7I3XyBGsfQ/TG1HBp/VR7sW/TxAvpbYL/pyf6WqDbrfAR/L8AezwZ6IqXJJKxWsO/2P8yjAi85r5btVuq2/I7Uk/ub8EtiPZPCfkXr7cXnUJ2JK8BqgDq2n/NSnoTnmHUcHpukNGC+ILJO5iuK9BOcnjHYkMQ6zQ1kCwcjTt/SOgg3iG1QLxfLFJlj2tlZGOYfksNIxlZ2zro/Xj+dB4c2tzrnNunnZ110fGrXmrg/1~-1~-1~1754647945; bm_sz=7525566E6BE1D3F1EBD83DA7DBBF40A1~YAAQS2DQF0TPdoaYAQAAacn0iBwjMtpTOFaSCmZwMdtJH4iAEuNh5UpvEwv9oP6nLj1eGN/n7GLnItzePTv2rq/QpCWIrYMTCGAh1vLz1+H2xb4ajKUCw9fVTPY8VR1JXx7C8D+D26wn149oyORsiWov7oh1v9SvFu3K6PH7NDMB4HWB1B+iQ3Zx4DWCXDjW8njhYQLKZ9j6E5slvAUTf7Gwy20hjwuIc/7m3ZThs2dsC76iuA/gaMNb/SI92tUP7DbQhrBwOfdYR0jZY7C3w6z2Al81XlZiQp81BjgpTxYlNTEIJbkkeq2hNqAjoKakBO99uHXRLJmdgnwPMoEySbNSl+sFy8InbreB3phY8N2Vcgp/4jJCxEdD9JnuQnUkm3m867Flc5ejX1OdVH9GFDI+aK4LVEvGOAtzHD0uWuf0wuYqm1GS0ADQ0FUHcVMWrrEV1CNK71wJNGAQ33Nblk3k5O0xewz7gmq8LOBX6g=='
	}

	resp = requests.post(zenrows_api, params=params, headers=headers, data=payload, timeout=60)
	json_data = resp.json()

	with counter_lock:
		color = json_data['data']['product']['colorName']
		source_link = 'https://www.levi.com/US/en_US'+json_data['data']['product']['url']
		for info in json_data['data']['product']['variantOptions']:
			upc = info['upc']
			if len(upc) >= 13:
				upc = upc[2:len(upc)]
			price = info['priceData']['value']
			size = info['displaySizeDescription']
			variation = color+', '+size

		with open(write_csv, 'a', newline='') as file:
			writer = csv.writer(file)
			writer.writerow([upc, price, variation, source_link])
			


if __name__ == "__main__":
	get_products = input('Enter total products: ')

	total_pages = math.ceil(int(get_products)/36)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(0, total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

	print(f'\nFound {len(urls)} product links\n')
	
	
	# urls = urls[:1]




	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_code, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product codes: {counter} / {total}", end='\r')

	print(f'\nFound {len(all_code)} product codes\n')



	counter = 0
	counter_lock = threading.Lock()

	total = len(all_code)

	with ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, code) for code in all_code]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\n\nDone')