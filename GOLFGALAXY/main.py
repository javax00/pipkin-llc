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
import time
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

write_filename = "final_golfgalaxy_" + date_now + ".csv"
write_headers = ['UPC', 'Price', 'Variant', 'Source Link']
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
	# r = requests.get(zenrows_api, params=params, timeout=90)
	r = requests.get(target_url, timeout=90)
	return r.text

def get_product_links(page):
	# url = "https://prod-catalog-product-api.dickssportinggoods.com/v2/search?searchVO=%7B%22pageNumber%22%3A"+str(page)+"%2C%22pageSize%22%3A144%2C%22selectedSort%22%3A5%2C%22selectedStore%22%3A%221419%22%2C%22storeId%22%3A%2210701%22%2C%22zipcode%22%3A%2298125%22%2C%22isFamilyPage%22%3Atrue%2C%22mlBypass%22%3Afalse%2C%22snbAudience%22%3A%22%22%2C%22includeFulfillmentFacets%22%3Afalse%2C%22selectedCategory%22%3A%2210051_1714594%22%7D"
	# headers = {
	# 	'referer': 'https://www.golfgalaxy.com/f/shop-clearance-golf-shoes-golf-clubs-and-apparel-1?pageSize=144&pageNumber=0',
	# 	'Cookie': '_abck=01B05B3071D9EF511CC96544C027CC23~-1~YAAQRmDQF2jQ1g6ZAQAA0iLXEw7+Se+BRxYQ2/2wX4GJJGqVDFTe5CLJZ1pIzFmQF9gpk+4BotSmQnIUK0NaPAsjBXUomeZaEHguL/kdPz1XDw9SAfdp2VIMKHF1AY7K/2adHWe5Wageb646mW11+sFCsAqoMRXQ0Xbb/x773x6BE9VCLrZu9nI7oBm4H3Jo4TzmECS8te5psKoSwqmO7la/qIOYgG82etxpuwkX7HeK9ScjLEb6nwfx5jv3H4AHeJjJiEFr93Z0czXc5YG7rqAoQfo90sNSWKo3lH6/v5gILij5VSlOacpI11kJ9GjBTalMnw62VyJgnmzxcAgPVmB/nA29DPL1Lp91/6gFIxxArgCA6kg6dhgG+uEEzzV+SPE71eWbQgfn+8d9tFkSuwDoKOHSlaJbyOQCoV5FZ583opwWVrTihu5fycXuCfYiG3RdVLzq8CmW0L7qdEE0rdOaVn27ra9hK/dGHg6XSBBSWe9XwVasm+EpDHf2~-1~-1~-1~~; bm_s=YAAQRmDQF2U51w6ZAQAAaljYEwRPJ3U2ZwFbp6Z5RMfkW3y/iBuN56YrJNOkZ16QBmmQP1LdMJrm56bI8FfBvsbvKnAIWtxfCtk/t6cDoxBgfVT+FRLmDncvBkPs0riwhQF8/B8mTLGPHMR5S6eeh65y9T1A1/9BJdIvqT4yzv4YJTcDQP8WQVg1DUioeee/5CmVsCaCS5PYrYvgCrgxSceHlLJXwI7kPslt3Udg/+e504HEh7up1Ti+9POer9gHTn5dOBjKAGk3dIsfpJp/aCIaJgfz+rwIGHiphnvaHDRIfA1vRWdJdpqF6SekKEEA0UzDBLS9joYMNAc7VMJ2vg6t12UWLtOsflSaNRW2AKpKwfmROYhquxRZGSv3sjD1YQ2TWfv9x7EIerIgLoWsRSXkEovNMInt+KEV/fs3Ns794oAP+YCO0X3611OmNtKYDLnpEtFie5s/Mf3e3j1F3496QMOmPS6/cQP5GVEev2DwsURXn3MXQrgBR10yXgcQnP+glK0TpB3Jov/i1SY3lwUALlr3gSpZBJJ5vGzM79aRxC9seNDDQgKMxwoY4KTLhxk=; bm_ss=ab8e18ef4e; bm_sz=91FAD8873DD49909C5DEEB5399D57B78~YAAQRmDQF2rQ1g6ZAQAA0iLXEx3OHR81aepWC4HeprPFMbrQXq7jd76hjwcItUUTb7Wff2ljdLY/MS65RNYcOABBR2NpeG0YFphDzlTGw1scV9AM9LPC+y25Yw/7PSQboEHNUrS4zXGNUuUpIEYg8iFExBpjTAR4a75hiaFK3Y2kz2rFUKRsVWp4FeGwUP5IQWO83VBBKKFWhR9gGH/b6LTgl1QRnhkul4wkAQ/UVht390CxSnM5RvCtv4ZJSy0MpT4QSy9iszI/EB/T/lSNpFfA74jKElZM+sUCsqyi+BTojn0FlbchzR4gpfPhz4Xc48650ASnGMwozPAnxqwth+8yPHw5OjL1PLn0M2+jWbfwCOYph2YcHLrVIw8AKkA/TScxIITnRHbzlLs=~3294276~4274501'
	# }

	url = "https://prod-catalog-product-api.dickssportinggoods.com/v2/search?searchVO=%7B%22pageNumber%22%3A"+str(page)+"%2C%22pageSize%22%3A144%2C%22selectedSort%22%3A5%2C%22selectedStore%22%3A%221419%22%2C%22storeId%22%3A%2210701%22%2C%22zipcode%22%3A%2298125%22%2C%22isFamilyPage%22%3Atrue%2C%22mlBypass%22%3Afalse%2C%22snbAudience%22%3A%22%22%2C%22includeFulfillmentFacets%22%3Afalse%2C%22selectedCategory%22%3A%2210051_11797599%22%7D"
	headers = {
		'referer': 'https://www.golfgalaxy.com/f/our-top-deals?pageSize=144',
		'Cookie': '_abck=01B05B3071D9EF511CC96544C027CC23~-1~YAAQRmDQF2jQ1g6ZAQAA0iLXEw7+Se+BRxYQ2/2wX4GJJGqVDFTe5CLJZ1pIzFmQF9gpk+4BotSmQnIUK0NaPAsjBXUomeZaEHguL/kdPz1XDw9SAfdp2VIMKHF1AY7K/2adHWe5Wageb646mW11+sFCsAqoMRXQ0Xbb/x773x6BE9VCLrZu9nI7oBm4H3Jo4TzmECS8te5psKoSwqmO7la/qIOYgG82etxpuwkX7HeK9ScjLEb6nwfx5jv3H4AHeJjJiEFr93Z0czXc5YG7rqAoQfo90sNSWKo3lH6/v5gILij5VSlOacpI11kJ9GjBTalMnw62VyJgnmzxcAgPVmB/nA29DPL1Lp91/6gFIxxArgCA6kg6dhgG+uEEzzV+SPE71eWbQgfn+8d9tFkSuwDoKOHSlaJbyOQCoV5FZ583opwWVrTihu5fycXuCfYiG3RdVLzq8CmW0L7qdEE0rdOaVn27ra9hK/dGHg6XSBBSWe9XwVasm+EpDHf2~-1~-1~-1~~; bm_s=YAAQR2DQF1E6SwaZAQAAZGIZFASmCr9JRWH8MgflSiT05JquxP3tb7pzC71tIFuBwF463EiOQ2pWQ6n4TUE/i5dZOolojeRbOXM6Gp8dMm7ZBDph6CCSkrAgy+cx0yTnH1qcsUDG4u3cCLQLELpDLYF8QPogifhaK6jBK6DeIso+X3MlOjy9+xIE5mWOs5neTOc80qGXE9/28Hc0Tv6LzFYnFGa50PCilngZzCeM6wvKr7WrpMWQdrI7XC576NxZ9YT1ok4OKvmjM46JWG/AdsJhTHr8fF2HaqLQlZukvhx8alV6SYQ5RWGJ0taYaUzK4+eFzctWtv1r7WqAKb/v4udOdk4riv43Fs2FiO0WP1r+KHF2X5EARCLbu5tDCIhRMlBYtgEKhg0Ig/gdJ7wSP8OhRi0hfBb/VETZQ5k91sNnZxOfW+B1gTfamgx31CrL3neKgknqpwpPNPjwAkQDGbaWPHr9U18fpUuavmaVikVuuckvULb2yjDH2qXJWZecCqMNlzW4TOe9IniwmHQDJLuSs+bKaZgMM+SrXGSqTvfmCOdAK3Gx3sHS8FcgkboNayOL; bm_ss=ab8e18ef4e; bm_sz=91FAD8873DD49909C5DEEB5399D57B78~YAAQRmDQF2rQ1g6ZAQAA0iLXEx3OHR81aepWC4HeprPFMbrQXq7jd76hjwcItUUTb7Wff2ljdLY/MS65RNYcOABBR2NpeG0YFphDzlTGw1scV9AM9LPC+y25Yw/7PSQboEHNUrS4zXGNUuUpIEYg8iFExBpjTAR4a75hiaFK3Y2kz2rFUKRsVWp4FeGwUP5IQWO83VBBKKFWhR9gGH/b6LTgl1QRnhkul4wkAQ/UVht390CxSnM5RvCtv4ZJSy0MpT4QSy9iszI/EB/T/lSNpFfA74jKElZM+sUCsqyi+BTojn0FlbchzR4gpfPhz4Xc48650ASnGMwozPAnxqwth+8yPHw5OjL1PLn0M2+jWbfwCOYph2YcHLrVIw8AKkA/TScxIITnRHbzlLs=~3294276~4274501'
	}

	response = requests.get(url, headers=headers)
	data = response.json()

	for item in data['productVOs']:
		url = 'https://www.golfgalaxy.com'+item['assetSeoUrl']
		urls.append(url)

def get_product_info(link):
	retry = 1
	while True:
		try:
			headers = {
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
			'accept-language': 'en-US,en;q=0.9',
			'cache-control': 'max-age=0',
			'priority': 'u=0, i',
			'referer': 'https://www.golfgalaxy.com/f/our-top-deals?pageSize=144&pageNumber=1',
			'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
			'sec-ch-ua-mobile': '?0',
			'sec-ch-ua-platform': '"Windows"',
			'sec-fetch-dest': 'document',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-user': '?1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
			'Cookie': 'GG_HIDE_OOS_RC=true; GG_HIDE_OOS_RC=true; AdditionalLanes=12,18,43,14,60,85; swimlane_as_exp_gg=71; akaas_GG_AS_EXP=2147483647~rv=71~id=4212dfd2ea524d7eaa5b41c21d6e61cb; s_ecid=MCMID%7C08504514819864240743347274809951468389; DSG_UID=3c14987a-5b47-40c4-9c76-b35b2047f624; r100=0.24; RES_TRACKINGID=721068759862062; _mibhv=anon-1754486316107-1526726920_9231; ndp_session_id=f1d11510-f134-4222-8de8-23b3374da494; _scid=48SsglC5srhxfaBp_E7JQbfZaALcf5Hc; _gcl_au=1.1.929147297.1754486323; cjConsent=MHxOfDB8Tnww; cjUser=8e3c6c19-a000-4531-80c8-38b71c581c8e; rskxRunCookie=0; rCookie=hxb932bw30s4wyohv9z613mdzzuvoo; mt.v=2.2136011606.1754486324021; __attentive_id=ae7f7123a7234b40942bb8803fbeb236; __attentive_cco=1754486324096; kampyle_userid=1c02-0b68-a7fb-da07-5bee-9c88-b584-27f8; BVBRANDID=e40251bd-c2bb-4bbf-b2f0-ae74930f71a2; _tt_enable_cookie=1; _ttp=01K1ZRHF9K53WXMQ6FZ8GCHXXF_.tt.1; QuantumMetricUserID=92e93b90001e7418d1bc1b9350aeb354; _pin_unauth=dWlkPVlUTTJZVGswTjJNdE56RTBOUzAwTldGaExUazROR0V0WXpsbU1qSTFZVE5sTUdVMw; LPVID=FjMjQzOWQzZjYxN2U2N2Yy; styliticsWidgetSession=85ca5da4-b9dc-4cce-b3ec-755fd36eaa35; checkout_continuity_service=7322304c-b9f9-4992-8039-63f13f1e50ef; tracker_device=7322304c-b9f9-4992-8039-63f13f1e50ef; tfc-l=%7B%22k%22%3A%7B%22v%22%3A%22g83pug6q6heib7jrcds5ksphpt%22%2C%22e%22%3A1817385929%7D%7D; _attn_=eyJ1Ijoie1wiY29cIjoxNzU0NDg2MzI0MDk0LFwidW9cIjoxNzU0NDg2MzI0MDk0LFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcImFlN2Y3MTIzYTcyMzRiNDA5NDJiYjg4MDNmYmViMjM2XCJ9Iiwic2VzIjoie1widmFsXCI6XCJmYmNkODJmYTMwYjE0Njg0OTRhZWJiMmZlZGQ2NzE1NlwiLFwidW9cIjoxNzU0NDg2Mzk3MDM3LFwiY29cIjoxNzU0NDg2Mzk3MDM3LFwibWFcIjowLjAyMDgzMzMzMzMzMzMzMzMzMn0ifQ==; __attentive_id=ae7f7123a7234b40942bb8803fbeb236; DSG_VH=125; dih=desktop; modern=true; gg_perf_analysis=NB-0; adbinf=e65e823d46ab958417b69dae6b704bd3; PIM-SESSION-ID=u5Fle6M8NYXNjVb8; AMCVS_989E1CFE5329630F0A490D45%40AdobeOrg=1; AMCV_989E1CFE5329630F0A490D45%40AdobeOrg=-1712354808%7CMCIDTS%7C20336%7CMCMID%7C08504514819864240743347274809951468389%7CMCAAMLH-1757577099%7C9%7CMCAAMB-1757577099%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1756979499s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.3.0; kndctr_989E1CFE5329630F0A490D45_AdobeOrg_identity=CiYwODUwNDUxNDgxOTg2NDI0MDc0MzM0NzI3NDgwOTk1MTQ2ODM4OVIQCM34ofyHMxgBKgNPUjIwA%5FABvLfXnZEz; deliveryZip=98101; akaalb_DAPI_ALB=~op=DAPI_ALB_WEST:DAPI_AP3|~rv=43~m=DAPI_AP3:0|~os=23e4831c4c3db7faf5739e09fcb415fa~id=add1a60366a06f8dd116f43226e6fa00; setStoreCookie=98125_NORTHGATE_1419_4; DCSG_NGX_CUST_STORE=98125_NORTHGATE_1419_4; LPSID-18232016=Xta6iRL1Q8Gk0TGRUmPe7w; _ScCbts=%5B%22263%3Bchrome.2%3A2%3A5%22%2C%22289%3Bchrome.2%3A2%3A5%22%2C%22611%3Bchrome.2%3A2%3A5%22%5D; __attentive_dv=1; _sctr=1%7C1756915200000; __gads=ID=a922ae0fa846541b:T=1756972326:RT=1756972326:S=ALNI_Mb2TajiFpYC83RlvSB-yKLpo3bgEg; __gpi=UID=00001267bb6f1ab2:T=1756972326:RT=1756972326:S=ALNI_MbjWMDiMVqiu7MhrPlzHkhgqnxBpw; __eoi=ID=e374c651af9be711:T=1756972326:RT=1756972326:S=AA-Afjbe-1FnreUrWnBekRzqB6-y; authPromoId-GG_FS49Login=10560565; kampylePageLoadedTimestamp=1756973985513; kampyleUserSession=1756974112300; kampyleUserSessionsCount=7; kampyleUserPercentile=45.1408602493231; QuantumMetricSessionID=8ed1d58a17017753f009710ff6ee4871; kndctr_989E1CFE5329630F0A490D45_AdobeOrg_cluster=or2; whereabouts=95101; bm_ss=ab8e18ef4e; __attentive_session_id=ee0385e7719f412280ebf17529d98069; BVBRANDSID=8f0ea992-f478-401b-a747-534d414662de; __attentive_ss_referrer=https://www.golfgalaxy.com/; lastRskxRun=1756979062127; _attn_=eyJ1Ijoie1wiY29cIjoxNzU0NDg2MzI0MDk0LFwidW9cIjoxNzU0NDg2MzI0MDk0LFwibWFcIjoyMTkwMCxcImluXCI6ZmFsc2UsXCJ2YWxcIjpcImFlN2Y3MTIzYTcyMzRiNDA5NDJiYjg4MDNmYmViMjM2XCJ9Iiwic2VzIjoie1widmFsXCI6XCJlZTAzODVlNzcxOWY0MTIyODBlYmYxNzUyOWQ5ODA2OVwiLFwidW9cIjoxNzU2OTc5MDYyMTc3LFwiY29cIjoxNzU2OTc5MDYyMTc3LFwibWFcIjowLjAyMDgzMzMzMzMzMzMzMzMzMn0ifQ==; bm_lso=FDB462F01B1AB0E10D07419681FB5658BA35B634176D626D81D7F4404CAF7AD8~YAAQkfTVF3akZfOYAQAAV9ccFARZYfAAx1A9LO4uG8fkVq0TxONzlj3PF5O1/jN1k0csm/tAJ9NQq6XmUswDDhYDScwKrhc+7fRFHhAiU3Z/D9PAeu2v7/RuGbDHzs8OE2jxovlUf/R+GAint0m31pXT//dBop59EvOXRQTrGeauKY9OdsK+17kH6Vdb9rkLBW7dXfOPrNrUt0GvCM4ACniKMemATDtXYY940oMu6UbeHMkXojR2OcUBoGPhzM5nqpEFs2WVuZ2FRkP4AqjAhA9ErbPOHy9QVB1FrYHXMpkxQvZLQ/h3EVmAzk02OZe6KG/6EvwvoO/uoat/ooRd3QPW3027iMVOBfTgJdy8yKCq8JCt/VL6h/sCIWPC/VGRn2EBPGQ3QXr+Zw6vxKNNV/7qpuw4K85ZL7q2qDh28UX+Mf5q+pjV+peWGupTtTViGCVres05FAskx51B07cHZzWL2g==^1756979062353; __attentive_pv=4; _scid_r=4ESsglC5srhxfaBp_E7JQbfZaALcf5HctzbWkw; _uetsid=09c31690896411f099f06727a05bc0fa; _uetvid=e0a107a072c711f095c77d7a60927487; ttcsid=1756978609477::W7mgoptu8eiMLP8Xdey5.4.1756979063473; kampyleSessionPageCounter=5; ttcsid_CHHSDN3C77UCQ06LT9C0=1756977655754::_DZF25d3B5-1A-l_bR-H.4.1756979063700; cto_bundle=aUowkl9oWkxRanRRS1hTMTBuZ0JxblN0TE5EOVZkUGklMkJvYW5KUFglMkJhYVBwd2c2Q3pDRTNxclhRNjhaayUyRkF1RW1penVsa3VkdkdFRXM1RUtMQTdKVFZ4QjFmNWRMbks1ZzI5ODlQNW51U1RmVWFPbjZBSnJ2ZGRlN2hyTk1KWCUyRms5VlZPelAxdEMxTG50Z0FzM25BaldlQSUyRjhJd0VWZ2slMkZlakZ4a2pnUU9UM2VrWUkzdCUyRlFuJTJGZlNBVGZKcWhMeGNXam5Ybzh0SW1jVkZTTE9vR0p1UWkwblMlMkZiVldUYXd1Rng1ZnZ2RlZLUW5NUkNEMlJ1U04lMkJ2cVppdVdvZ3l3SVdBb3cyT0tQVGFqcHE3U3RGJTJCdFZFcTVzWXhscSUyQlRYQ1FRTkRmYU9jZHNFR21OJTJCQzVocGVnM3l2MnE0Z1dYWnZ0a1pv; X-DSG-Platform=v2; ak_bmsc=75425BB7F7844F375A7B1F6A91D9CDBE~000000000000000000000000000000~YAAQkfTVF0yJZvOYAQAAyuorFB2G9AEBlk1GbfpZngOQHoBcM+LdUaNVsVwFIRs5Eg/gi4ldNXSAyppJEN1ZzSS2nwkT70jjzwXA2GriugpdS5kV/2L64WsryoStLvZV82rzmNm7IKcNYXDS9yxGje4sBZv269WR1DywwvSJ4PYK/dF6i8uH/plLtfV4Tx5ila6R1I3tETn5jW+B2OjTR3qk4k3xSpYTXa1qwUrrJyJLnnMR617ZyXhBEeuMSCUyh+ZFIgIpIp1prBCMwSKuWRFS9zKXU4udyPkGk/QibhIYrlFqnjLm57A45YehMCukQa1UdA2bu/TNb5IK+KnvS0cwIJqLHFatmRJn8J1UmwqpwHg7CxaY0s6RC68IF26fQH0i6DmdqejGVvU2Z1E0Qkw=; bm_so=FE2FBE866DAC2AE10B179D28203332A958D91260663AC29E1C108F6EECB291B1~YAAQkfTVF06JZvOYAQAAyuorFATuoMLMq1o1qzpmYidtzAQu7UiJi8hiMNfsJ2Pp/dgR9TW6M/eoKMID66pwCJk+Nfg0neUDubMj5IsCFo2j3I/E7gAgT1rCOrJ9gPT8Of7R0zHAH71yMtGCOnS6fcZaveIIxbImlTRMB9zeYWtIiLxaf0Vm4dWUbNbd0SRqF+cI8JlVjSWTpLAusJlLXlu+CgJ9PhpUIDjldffB9BxQLhteLzjV0vfWG02rcB1Dsd1TO8JLXSt+1pkUVU0xUvrSuJVYyo7WSvIXUcrdn++H2QekcHB4Y74eI9RopYkjYZ1cscUH0iRpJc9LC3Ei8qN6emv8LvM9g1Vqoh6sxOTN99sjEY6170EApVJ4dQnMjXP4JAR2M2jbjK/BjmO6UWbjVxepef3XDbsUZ+iaZXRRe5pIb+Bw6Hlrd9fOaFhVXvmoDNhbmNf90PGx4VGw24bK+g==; bm_sz=B007A129CAC133F75E34A4A0FCC7A563~YAAQkfTVF0+JZvOYAQAAyuorFB1WCzHadPOaLkccvwauonUzu1BCRWmdHVltyFgHnXqObp3CTLcRuc5VeJdfVvGuu5qc6oaLCSE9+3yKEEBb5s3iQsxAQXu62uRXeITP4KVS7XnNnRV0UIWbju0jc3e459AyAm15GPbJeVGufD0BuZC3F2MM4uZ/GWO3zjeTkaPBxF3kpqIs1zdoIXE9fjhNpcp3qPmPdoLW4Qwk6oAGgGA5Dbhe+M86JXcJ2XN1/cLGvY8tpcHkPeAzc276BcSPqwPzQ6uQfuNshamlgpg+03L5AzbUg4PgTEAev6Q6md3WGfxl1ALXvtv/6gGBLYl6VOrEKIQ/a4KxkKCmMKhCo+5OhmgPDNvHc8poqXadh2faNPo/l76jfxEv4Du0TboDrJXqz7FEETcraGFFn/VcUO9bJ2c1GSUAHMaPHTkLcFwmP9iiYEkWuZOj8OrgU1orK8C/pPUR/Lylv75b/y0jjMdj01IDMNwK/jlehMMzDhnSU61d/kqYFOu9IAg3THcG30Eegnl/Dv480US5ToULN5cEgxFtpmKBvfyZ1D2G0ndFM94p8RwUK+H9~3752496~3421763; _abck=941D695601E8B8807323F602198427DB~0~YAAQkfTVF72JZvOYAQAA1PArFA6Vt/TSbeIBarQqusBJkm0yPP6Nz7UntQzfv12Zg6BCsDglPsqkF4R8mW7WX3uVJxjo4/VDDJKCWOjrfU4rbdWyYpjy7OGcUWnpOOIeCLCPB9+ndIKy98ESsefqiWpdKRtgsqXsHD+spimaInMyeX5T2oQ0J5BwYAmaD2Z/zDk6XxlSpGRa1UcPCX2fHguunnwIWYkUKGjQ7loR3vFhrHfID05qtjMXxvrpZib7mJ4mF3S9bSDiwHp9xymdmOibudaN+hDahVs/JaJmIlXJhefEodZO1Ny8JYaWiXFgxsybBt2ix8L4xlS+ydno6fT5pnYhoVXAeVruEkzclM8hipvB/MT68IJQ5CjmdWRaABUZ91lipE62MQKwwbj3LtB+HBvr0kQy8/EPWnqSpakVFwQ59FrXX7VcmnGlVnK5RQm7XuiEZjXPIWdz/xlJqJAHWQDQNzWvrquX0VccQPlxNNAUXRzY8TNhFueEUFEIk0tltrGNY1q6NGgTwaX04eKMomJkhs1OwVBpmLo9OLfP5PrZWAqbT0UIINvtP2BjHfW82xIF/4Clx6VFQyxGIbq7xnZMjlQV2X353+r368DWlsXE2XfRKVxMI+j9qa9H7zgMf1yawS8IYiWFmp8xJzFEzQx41jN1KbgKTTyOVr0Xlg4ziCvVfhoOlrxsgpFeaJT9H7ambeGpyUhEo4sKrfoMz0LFfCAOGwb1aHGAMe0cRnKS1hISjR13xrLA+dKOwoONXOJOZIAWlfJCjPgKpWFQi3DcnKRP5ztt~-1~-1~1756983109~AAQAAAAE%2f%2f%2f%2f%2f7+o6sLI7lxzhDg1mzUMXCZNe5AgvDuolQMS9qgp+5GZKc+lRyH51ZCzIHMFyLFIlHigAixmn%2feQxysrvKSdVutLAh88QaxvnsHmcGpnZe6iVaXcahZOYMmuzN469Qm9cYWra+Oz9%2f4Dv5Q4iXht+zethCQA8oOj6Wwl1yRtcGyl3V+RUC933sV8bHhxdRw3b32obog8XLZ5~1756980362; DCSG_NGX_CUST=%7B%22accountType%22%3A%22guest%22%2C%22sessionId%22%3A%22261722f5-94a8-4ef7-a807-e1af00a4e19a%22%2C%22userId%22%3A%22-1002%22%2C%22visitCount%22%3A17%2C%22expires%22%3A%222025-10-04T07%3A52%3A19.103Z%22%2C%22isScoreCardGold%22%3Afalse%7D; akaalb_scpps=1756980349~op=myAcc_scpps_PROD:myAcc_scpps_AP01|~rv=40~m=myAcc_scpps_AP01:0|~os=23e4831c4c3db7faf5739e09fcb415fa~id=e5778bd0d582ae01f060c03bb561af02; s_pers=null%3Dundefined%3Blv%3D1756980048179%3Blv_c%3D1756978609509%3Blv_s%3D0; TAG_Direct=1756980048219; bm_s=YAAQkfTVF5eKZvOYAQAAIPgrFATaj3wSJbWvfynZPyAzoGh6Pev68jNwimHAKzCEM4zV9IEVNSK5mKMoifJI3Gy72KOX0HfKnx1pGYFUS5fpWSKz2ukdY29M55v/4omciXb+2Ps+KMVBdpN+9kuW6hDdE1q44x4LKdnTOnJQ20xDBa0FPSVgrbwVwK1YxSKKihLRrDGCbYPn19+uJlrvxA65FpCrn4DvOr8YKvxSPmIZBjAYyYUQ11jAgAnsAXugLRkQg4Rr/pjjZNis3AOg5omLSd1jv6XDo91wc72Nmgk0RsJjG0C/v+hLL5+SniyO38N27XyZFzmcvVfiKI7M8zQ2mJBzJurHAeFGWhcPp1HW7CqwLso0IDtEqKB64/yRfZvZYc4zI3lkv5fMqUyX86dN7FprE/va1biEDxc7hmc2bdwC9XMquh5+SRbzSWY91G2EpGQXiVmQnL8dG7S6TQ+AXeqVck659KRpcDo26HNHnxZelqPqGlBXKFBorQ9phdgxWyvB2unyNhvEMODfis2b+sElNp3re1oB1dLSsPiXNu3BQFHiIm1PmwC1dUfu5Wo2nMshsRMr1e0=; bm_sv=3E13B5ADF260D11471AD966FA9E26D28~YAAQkfTVF7SKZvOYAQAAnvkrFB0hS8GzDtf7dMCrIexIDqkJf+vixwwo+ErTZBwyW28WMWC5JHSEb7HZ2SEUB19+AXXHSRDxycM3ZPeqbFTCXYjHuEDiyh2/uqjftfhWJlV25F4W0OQRGnYZsp2ED5jZ1yVzgQIbS8sX5ei8d69tNvldpq3GRH6YgJIFknJkwlDadldYCa9mgOPfN2LpaFGuEsl/+XJ5wZ9x0k9ui6hRXaRZOrLnucKiCaI5qseFcPbS2w==~1; RT="z=1&dm=www.golfgalaxy.com&si=219c3a08-eb52-469b-ab99-6e48defdb5ef&ss=mf57y5em&sl=3&tt=4aa&obo=2&rl=1&ld=ly0r&r=15737hkr7&ul=ly0s"; GG_HIDE_OOS_RC=true; AdditionalLanes=92,45,90,41,97,12; _abck=941D695601E8B8807323F602198427DB~-1~YAAQkfTVF3OPZvOYAQAAY0wsFA7siU80yPkDKKtXwaLqok/fw6ueB8BnO0dElweLfmXBhyK1YIqGpfHuU6xR00tNDC8HsXa7uqcdC+hbuexmHM0ckao7lgK3FFh+jprlRFRsGtyvGp+oPrPMggWrSfZ5NpOLJWiGBCNeokDEAyuBFK4OYxRdgUZ6tlRW4WH74xNexJenPkYnNVtbXcieCF5v2ABRAw1EiTkNJE9QzVz3fubl/QOX5x8TWnVXAGzr0ggbcWN1CB+9CCbqEO4dLly607OqtWhvcwj+JbsL5PczUtAUm0ZDRwZ2GVf28RIKTH/JuHyqdoxQRs6aAM4dwk+YSv/l+1HSiwkGYdjC1WIixcf2hk0bZNIo0pbL5Mtm8VxbtvkwvNRlcNlUKcWrnV1IXcv0pNt0sHkdZTHboxPpv8RJspwpla9v6N1E8fLG7anK2uWII11kZEEmGZFbx+uDzL2gcE6mB+GgaX6tVs5F/ltHEhQzqMrk13BR1bTFMwroZOn8Dzf6A06iGjtwMbdacPaYGC0AxgzC6CCj9tLn/MPzSf0k8x7eW+gx9Ydm0gh8mtbK1KxlrkZ89Ek3We/piNcK6McuX0jxjXzoROS/xxfEGDoMzZ1D7FZiJxYY5a8wfp91ptk8WlaaMVylY+gWnc4VE7I5I7rH8NJeOcdo5TajpJHqiKDSo4GEQoXXf+/IJSg9AHI8qwFzVamtnW7nSatyY55vYZQccOPX/Zw2xewgzu1g11esxBMMlvYEugKtvxULxSbsSenHsxFbU4lCpB8o2theChdKPlI=~0~-1~1756983109~AAQAAAAE%2f%2f%2f%2f%2f7+o6sLI7lxzhDg1mzUMXCZNe5AgvDuolQMS9qgp+5GZKc+lRyH51ZCzIHMFyLFIlHigAixmn%2feQxysrvKSdVutLAh88QaxvnsHmcGpnZe6iVaXcahZOYMmuzN469Qm9cYWra+Oz9%2f4Dv5Q4iXht+zethCQA8oOj6Wwl1yRtcGyl3V+RUC933sV8bHhxdRw3b32obog8XLZ5~-1; ak_bmsc=5321299C29BB5AC929528DA632554809~000000000000000000000000000000~YAAQkfTVF+ITZvOYAQAAMzUkFB2CyHvfmU0fOXsbHeplfRjOcBxt6DrQy9Riav5vme8J4r59xQegT44k17ELUt33m5dTAR9/z5MiFfK7RM66/OgJiOR7/chUodvUAmc/YtJe/UlNPlOOheN1chqa1cTsUkMxbGPPIT8Tt7kg9osWSuNV6Hjgv7ITr9tleCUqySqoFHmDjbhROhakBvQYnLwl+WD8X4yl3EARNtHUVkIpJ9AbLLdJNA8dL00BAbMkuuqzDK4Xj6kLweC26IcMlP1hBvXAYoid+zzyGaDdm085yE8jsl1movZsuNBRvqv84QUuTbDrWPXtLmF3wf+de4HKTYpe8F95AlfklIoHxv7I6w==; bm_s=YAAQqPTVF9nK9O2YAQAAxW8kFASdCV/h3P0T31I7T2g2q8JdegAoKaeUnmMM62F72EXoOyB+xsvBB+3uLPA57XkkX95ttlYWke3ytwQG58UaMDutNTNNqFqS6zExszps16B+6msI274gH/FlVNnwrjECitjbr5oEZWpUK3hnXwbuRx8vl7ioN0kHu+gRpx9uk1o4uUihuNYgPjSdGTNXnRXGVRbMcWVs7BZbG1PoHHneOmfAxgypH4uqpCd6mQrXnr2EGY5YdVitJObEO/dnV6/Stpk2BgZXiDi7sNiRFEdxx96LwlsAKt5kcU0o172pjj9MkURWDM/xQZWf51058hWqVV5QoTypaZX9/riJVgNg4X04Fhx/xoOSV6uCXiQtXwM0Lq8nBViog6mmR5F3Ct9k4czPsOY9eynTKMbs3EJN8A1OjzWBdJUImWJNuAQTo4b67DK92fUOW7nw7OpeqbnFOm2CONv2Pnsmm7etYwZ3FVxn9K21vB0VDCRHRqtdXM07JpeYwDYpsRDvcz/+UbJBNx5EKfiDk1zRd1Dp6Q4InLzv4Ru0zJirkmolidBfQqth73l4j0zmmA==; bm_sc=1~1~662383654~YAAQqPTVF9rK9O2YAQAAxW8kFAVt3Cd7hDSOx54cQRXQQC4SbJZKD4+llMuxIL3PRrnR+3R9YX1Hc/xMwOo6z8AVAbb0aMPuCV7XaoGwdkW0CnvotUWKsjr20NogRB/cbxZjdVgfEu0m2fd5qKEoN1XmPX57EazB2SwgyF9sLAYlsvGfZGwBNHacOtjTeVvY6phIojdz/1L3PKVo23ObyYbdZuwOrrqYTKASaf0sOO9dLPnYqrgAcyte8FNiUT5MuSn6EqqTByR1pZowmvm/7y1371pGnSNbg9cFuAxUGSXlf0hs4+k7SRKmRTcLEVMiPfqX1GdP+GWyUYNu4JASyZ3gQIF85Uz07C4ia+aMyRpbXcgtCexK+do1Zs+fwYx2lDTeN6q4whe2h7zT7CHUG/nAqty0tTu9u+MH1Q81qAdtxJOfokbdCL4m8XJWysth273oePYFUBthgM/yL/GBjdfLxzHqTKCrTSPTskdvqE/BXonsU5WPmXQycInC; bm_so=A63273DF326316527F75AA775D0CE7C68B31D9BE96811405A483A7094934F68C~YAAQkfTVF+UTZvOYAQAAMzUkFARjexd3/bw3ZcsdhnCA16MRw73v+JoYmsr+g6KWbi1DwlC3hblsgP0QPJ/fbtKDicVqAQDlyUa3br1yUxbG7Oa/q7vwL3926mByOWC3TFIWMS+1TSk9UQS5qbsst7IFj085dREKozTZjGgo+DYRxq3omGEawrwfPyO8wYS+bJnIkGMI/usW/Sj3+0AtA/eNsKyeOsAB9s+2GzSu/BcvYZICB65ZF6QwS85qiYQxBz+uRo0RSfjwrpfB9eomtvI3OtOks/bblHf111EffXPV8CK2/dEC/niHZlj3V+g3O5jtLqWD+qOQ9tBr4T8BkTDT1jwsEOTvteTma6lvMK8kJWz51frD2IoLk30G1fT55WB7tanCyEPsAkcOnaxThvRZO6ZywDY0rX/CyxEuaGSlkkVQmN9aPmqLNqq7UgLlvGNBhBnZf/K72O0YR7EfsvocEg==; bm_ss=ab8e18ef4e; bm_sv=3E13B5ADF260D11471AD966FA9E26D28~YAAQkfTVF3SPZvOYAQAAY0wsFB3kC4QrCK61e7WQQ6riiRHczX0yAo3YepYyI1IeE7tr/QIGtaHi1GPBCFRTT+7tPWCJMnK5+dTA3lvbQ101AaxQ7BaQQqipMH0APVOYx98K0jT+5jczUwWyFG+ciyPryCUK5nakbebWPOH16EuShlfX+q2m1DbnohS1HsdIL9BTZC9+HFFK1ihJlI2R9QXkrmo+7VD3UFg3z7DOVGFeUD6b0h8mk9mW+6dRkrefA7FmdA==~1; bm_sz=B007A129CAC133F75E34A4A0FCC7A563~YAAQkfTVF3WPZvOYAQAAY0wsFB01n0b6H+VZmYmTi8yfvGoe0Cf4Jr/4I3jWto9AMH6OGZSyXbH9XpIiifzYmSo9nEYf8TWCfVL8TGBiWD5TbIwJYnMlgz8q7nKYqiPGqhkpcf+f9oTtGaGcRBb5VQaiRsCpNYjVY2H8K1sdMtmyeJBIZlCg3m0JvYtHMG5VziY+ZyDBTcnTVZ7uS0IxeUOeF4zVDQoUASwAwDITLT3kQ6BzRL4g3lAknN0ZK588lxB/Nuccv7/Ez6T72a7RtD0xh54Aw89DaCcEWCvys3SIl41J/L6HRWiOSZt/sm5iEYncxoFc80JVo1LSZcYBDIxftv2fX/5uEULFQs6wtHCiN4AsQxOAwJMY8TfALzDSfa3iqOKUMkqqtaEDP9QCmtbYgBNkkSt8MpzTd4UOky4QDWbIw9nUQwLjwPsu7IA1YIBdWA+vRF6r7tMgYv8Ab2Q85i/+DmW8Hqsa/FcF0z9dNfiem0lAdEPCohBJvNqi0R3OFHlTeu1Mss8JpuMdPINzajhmiTk4dsiNLdADg2iSY7CXCJxE1dsHjLG1A2wlpR5aCfbOv0otucum/Q==~3752496~3421763; DSG_VH=125; X-DSG-Platform=v2; adbinf=098cc8f7bdb4f393864610952bddfbe9; akaas_GG_AS_EXP=2147483647~rv=74~id=d6c7292e03b1b1b19d85e94f7b5ab25a; dih=desktop; gg_perf_analysis=NB-0; modern=true; swimlane_as_exp_gg=74; whereabouts=95101'
			}
			response = requests.get(link, headers=headers)
			soup = BeautifulSoup(response.text, 'html.parser')

			data = soup.find('script', id='dcsg-ngx-pdp-server-state').get_text()
			data = json.loads(data)
			break
		except Exception as e:
			if retry == 3:
				return
			retry += 1
			time.sleep(5)

	prod_code = ''
	for i in data:
		if 'product-url-product' in i:
			prod_code = i
			break

	for item in data[prod_code]['productsData'][0]['skus']:
		price = item['prices']['offerPrice']
		source_link = 'https://www.golfgalaxy.com'+item['pdpSeoUrl']

		for i in item['descriptiveAttributes']:
			if i['name'] == 'PRIMARY_UPC':
				upc = i['value']
				break

		var = []
		try:
			for i in item['descriptiveAttributes']:
				if i['name'] == 'Size':
					size = i['value']
					var.append(size)
					break

			for i in item['descriptiveAttributes']:
				if i['name'] == 'Color':
					color = i['value']
					var.append(color)
					break

			variantion = ', '.join(var)
		except:
			variantion = ''

		with counter_lock:
			with open(write_csv, 'a', newline='', encoding='utf-8') as f:
				writer = csv.writer(f)
				writer.writerow([upc, price, variantion, source_link])

if __name__ == "__main__":
	get_pages = input('Enter total products: ')

	total_pages = math.ceil(int(get_pages)/144)
	print(f'Found {total_pages} pages\n')

	counter = 0
	counter_lock = threading.Lock()

	with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
		futures = [executor.submit(get_product_links, i) for i in range(total_pages)]
		for future in as_completed(futures):
			with counter_lock:
				counter += 1
				print(f"Getting pages: {counter} / {total_pages}", end='\r')

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