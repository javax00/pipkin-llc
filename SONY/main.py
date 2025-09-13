import os
import csv
import requests
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import json
import concurrent.futures
import math
from datetime import datetime
import urllib.parse
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

write_filename = "final_sony_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Source Link']
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

def get_zenrows_html(target_url):
	params = {
		'apikey': ZENROWS_API_KEY,
		'url': target_url,
		'premium_proxy': 'true',
		'proxy_country': 'us',
		'js_render': 'true',
	}
	r = requests.get(zenrows_api, params=params, timeout=90)
	return r.text

def get_product_info(link):
	source_link = link[0]
	price = link[1]

	html = get_zenrows_html(source_link)
	soup = BeautifulSoup(html, 'html.parser')

	data_json = json.loads(soup.find('script', id='ng-state').get_text())
	data_json = data_json['sn-bzv-schema-'+source_link.split('/')[-1]].replace('\\', '')
	data_json = json.loads(data_json)
	for g14 in data_json['Results'][0]['Attributes']['GTIN14']['Values']:
		upc = g14['Value'][2:]

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, source_link])

if __name__ == "__main__":
	url = "https://electronics.sony.com/api/occ/v2/sna/products/search?fields=CUSTOM&query=%3Arelevance%3AsnaAllCategories%3A1%3AsnaSupportedUserGroups%3Acustomergroup%3AisVisibleOnPLP%3Atrue%3AoffersAndSales%3Aon_sale%3AoffersAndSales%3Afree_with_purchase&pageSize=96&lang=en&curr=USD"
	headers = {
		'Cookie': '_abck=A5F56FF86AAAB7BB9345BBE163C5E49F~-1~YAAQbl0lAfcBVKyYAQAA7PlRuw6X9T7k7cHbBSVewk5uDQshoVjRy65QPiF/gdtlUse+bKJ3aM4uH1Lhy9XM0dms7HRPpg/1kw2GSYrFIs5WJ4D9ImewELP8B2iOUHoFG8u1qaOawsi1LJwd4t4fTYyj0K2ZoEhdS4HFxlhFZjiOPvsn9zkqKK1yGMFQtEmicW9dWHMrEqcHl8kJmZgDsrFVWWh+P5oD6OL5qD6DVQOq+RB099GhSs6DSh4OyhfBSza+5ynsFNc3TNym+ktxCcY1jSzSDxyU8iY3GYQ8cFJOoXbb6ewrGbPNXMBl9ZChtk/hu/nnOkL7bvcXrjhuZM+TXR+qLJ+qV5U4oaepT5hZz7qZ4p2G0CV8R4+Hq4EFY/IP6oGoc5ho11y+fcIyASX7Dl0AS9I2g0suqvSxWxx/+B176lrlFmg90TRjnvWwIqHgj96jbZCTeTkcRcHsYB6Z5ocbwnW4i/Vy6rs=~-1~-1~-1; AMCVS_7286403D53B6AA9A0A490D4C%40AdobeOrg=1; _gcl_au=1.1.1854163303.1755490154; _ga=GA1.1.1062804531.1755490154; fil_p31=; s_loginStatus=false; ajs_anonymous_id=15d85e05-3829-428a-aa34-c6298fec93b2; _meta_theTradeDesk_ttd_id_failure=failed to make request; s_cc=true; gpv_p1=; nvl_v29=; sst_v71=; _tt_enable_cookie=1; _ttp=01K2XNVZ8B2CJMW1DVRAPP8R6Z_.tt.1; fil_p31=; s_loginStatus=false; s_ips=1597; s_tp=7085; s_ppv=https%253A%2F%2Felectronics.sony.com%2Fc%2F1%253Fquery%253D%253Arelevance%253AsnaAllCategories%253A1%253AsnaSupportedUserGroups%253Acustomergroup%253AisVisibleOnPLP%253Atrue%253AoffersAndSales%253Aon_sale%253AoffersAndSales%253Afree_with_purchase%2526currentPage%253D2%2C23%2C23%2C1597%2C1%2C4; s_nr30=1755491598996-Repeat; s_cc=true; gpv_p1=; gpv_v89=https%3A%2F%2Felectronics.sony.com%2Fc%2F1%3Fquery%3D%3Arelevance%3AsnaAllCategories%3A1%3AsnaSupportedUserGroups%3Acustomergroup%3AisVisibleOnPLP%3Atrue%3AoffersAndSales%3Aon_sale%3AoffersAndSales%3Afree_with_purchase%26currentPage%3D2; nvl_v29=; sst_v71=; EMAIL_OPTIN=true; gpv_p7=pdp; ak_bmsc=6FADF6984461346522A3E92CC74E22CE~000000000000000000000000000000~YAAQgtAuFy7etLeYAQAA15TFuxyMZo4DRXd9Z8etgLdHXzk6wVBOQCRhcHme3uMSC4VgGfJKPEhZr42pM0xl08pJWUHhy0mHkntI3UnWGAj+ppkb2spfxeTeaLMtbuh3Xu6LbXeSzeK2jf2RTEqvOInJXQCV8LeEXCxNgl68XGWszfAiVw0+qaaj43UquSLYsPnC84iDEdmb98IOS1asZhPn1mZZ04exVGm9L82dr9FhGU2tAKwwALQHPJx4v+Jv6ROSaXoyIil0UbuOFgQ71TKi6Y4914QGDdFgA6SQqJYMZIidMCl1xH0Xuq79XNTHTcq0pEFli5CYDJcQnGkyO/5XPJgFUunYlhwZsTlFzkfPbF/KGPoZmSh7qmY5uab0fmo0zuDyKWyQ1w4S9Fx2Qs1GkVEePGy9VYhtJpz9SOnJFahLyvwsW3LOuII+9/OFacHzpPTom4Z6gl8=; s_fid=2BD36EECC2EEDE0F-099E16993F0EDB20; s_sq=sonygwt-gwn-eu-sit%3D%2526pid%253Dhttps%25253A%25252F%25252Felectronics.sony.com%25252Faudio%25252Fheadphones%25252Fheadband%25252Fp%25252Fwh1000xm5-b%2526oid%253Dhttps%25253A%25252F%25252Felectronics.sony.com%25252Faudio%25252Fheadphones%25252Fheadband%25252Fp%25252Fwh1000xm5-s%2526ot%253DA; s_dur=1755497926685; AMCV_7286403D53B6AA9A0A490D4C%40AdobeOrg=-1124106680%7CMCIDTS%7C20319%7CMCMID%7C09989636082096115462910321183631359349%7CMCAAMLH-1756102727%7C9%7CMCAAMB-1756102727%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1755505127s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C5.2.0; pageURL=https://electronics.sony.com/audio/headphones/headband/p/wh1000xm4-b; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Aug+18+2025+14%3A33%3A34+GMT%2B0800+(Philippine+Standard+Time)&version=202403.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=3dc4d23b-1859-4739-bbf6-2876553ce207&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&AwaitingReconsent=false&geolocation=US%3BWA; OptanonAlertBoxClosed=2025-08-18T06:33:34.645Z; s_ips=848; s_tp=4420; s_ppv=https%253A%2F%2Felectronics.sony.com%2Fimaging%2Finterchangeable-lens-cameras%2Faps-c%2Fp%2Filczve10l-b%2C19%2C19%2C848%2C1%2C5; checkout_continuity_service=7322304c-b9f9-4992-8039-63f13f1e50ef; tracker_device=7322304c-b9f9-4992-8039-63f13f1e50ef; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22mQ4B0pexbWhhKVpdOlAz%22%2C%22expiryDate%22%3A%222026-08-18T06%3A33%3A36.131Z%22%7D; s_nr30=1755498816472-Repeat; gpv_pn=sso%3Apdp%3Aimaging%3Ainterchangeable-lens%20cameras%3AZV-E10; gpv_v89=https%3A%2F%2Felectronics.sony.com%2Fimaging%2Finterchangeable-lens-cameras%2Faps-c%2Fp%2Filczve10l-b; ttcsid=1755495910753::z_4mgVuSU0q98TuWzUCI.2.1755498817524; cto_bundle=WTrd3F96JTJCYUt6TG54cmY2OHNJbWtYUkF3Tk1XRUoxcFQ5eWc1M3RLVUlEYWdoSm5IaDlUNzNkRXNuWVUxMzQzTWdYUm5qTFI1U1NkMW1kYWoyc2VRb2R1NUx1RThYTkRrSTJ4Q2w2R2tHaE0xWVcwR0UlMkZnR1lwN3ZvRHclMkJkR3diaVJDUGpQTnBuSDZiSGVINmFNWE8lMkJ1SEk1JTJGQmFIbnhiTmdFVVJjalljaTdRcDNTOGpTcnVxeUExNmZaWFBlQkZja0RPYkI3RzVMTGhzbWlYMjRWbGpNbUNkMGVWYnJJT3RNaWtRZnFSWDdiMDl4JTJCRjhKZVNwV3VmeVYwQVkwdEc0dGF3UzJyTURPSDVhanUxbHJzelFvT1d0OCUyRm1BR3pEajN5UnZkbWwxWWlnS09qV2xKVjVuSEVuckNoeWw1Ym9KYmRV; bm_sz=DAD5E0DF2ED121EE04A0B8C020FBB4F0~YAAQhtAuF79gjbOYAQAAqCfiuxxnh68PBS54ibsaXzObLstx/hWkbLRjkem7PEX9VG3eL8Fubvs+xoIzxVJh3NuaU9VuDn9UvcOH5WBGd7RiYY96l7grsJDSk5x3/QhpP7wH4XQp8ttZdcA1qDYUPRqFNrTvDncecjbY4oNSSbWjeSU+LR8Txdg59lAS54HyzRxyrsjhdzRahsqPLa1BssF0ia60BB/BUedNjmo31KRsEPh0vrFMM7nMaNy25TvJROFHh5DH4EamQrQikmKUcEB6H8Flzh8pMH/kyQaBoM0T2ZI3TZkMbESw1E3V3d0lk81kFiAgSnhi5REorlQj+jFi56dX6RM9KuehSfIqL9t9sYKsvKwZwAblz4QWOCwRtbnuBeZbNWyEP/gjXR78ucPVQAZWwItP3y0gkHn4mP1LPZqjT36Cg9uGGkCSwd3rk7UR3efZGojx+2olt24+cXB7qbMkz1YPbWvvY91tcf1hq8Ljm8QjnQl6aLNvR7lSH80mzo8gbNDA6NNR+KM+0S6ibonp9BAE7hXAuV6ZuIpElPlVE+KPU/kU~4403764~4605239; _ga_6KV0TTHN3G=GS2.1.s1755495903$o2$g1$t1755498817$j47$l0$h0; ttcsid_C931LB3C77UB71TGD6O0=1755495910752::3upVVh583oPFFpLj1WBO.2.1755498818041; ROUTE=.jsapps-8578bf7959-t7vft'
	}

	urls = []
	response = requests.get(url, headers=headers)
	for base in response.json()['baseproduct']:
		price = str(base['products'][0]['price']['value'])
		url = 'https://electronics.sony.com'+base['products'][0]['url']
		urls.append([url, price])

	print(f'\nFound {len(urls)} product links\n')

	# urls = urls[:1]

	counter = 0
	counter_lock = threading.Lock()

	total = len(urls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_info, url) for url in urls]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting product info: {counter} / {total}", end='\r')

	print('\nDone')