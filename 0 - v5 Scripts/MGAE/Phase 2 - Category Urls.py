# pip install requests beautifulsoup4
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor
import threading

# your ZenRows API key
apikey = ''

# input & output files
input_file = 'P1 Pagination Links.csv'
output_file = 'P2 Category Urls.csv'

# load all pagination URLs (first URL at A2)
with open(input_file, 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)
urls = [row[0].strip() for row in rows[1:] if row and row[0].strip()]
total = len(urls)

# prepare CSV writer and a lock
lock = threading.Lock()
out_f = open(output_file, 'w', newline='', encoding='utf-8')
writer = csv.writer(out_f)

def process_page(idx, page_url):
    # print as soon as this worker starts on its url
    print(f"Processing Url {idx} of {total}")

    # try up to 2 times on error or timeout
    resp = None
    for attempt in (1, 2):
        try:
            resp = requests.get(
                'https://api.zenrows.com/v1/',
                params={'url': page_url, 'apikey': apikey},
                timeout=60
            )
            resp.raise_for_status()
            break
        except RequestException as e:
            if attempt == 1:
                print(f"  ⚠️ Error fetching {page_url}: {e}. Retrying...")
            else:
                print(f"  ❌ Second attempt failed for {page_url}. Skipping.")
                return

    # parse and extract links
    soup = BeautifulSoup(resp.text, 'html.parser')
    grid = soup.find('div', id='ProductGridContainer', class_='collection__grid')
    if not grid:
        print(f"  ⚠️ Couldn't find ProductGridContainer on {page_url}.")
        return

    anchors = grid.find_all('a', class_='product-item__wrapper')[:20]
    base = 'https://shop.mgae.com'
    rows = []
    for a in anchors:
        href = a.get('href', '').strip()
        if not href:
            continue
        full_url = base + href if href.startswith('/') else href
        rows.append([full_url])

    # write to CSV under lock
    with lock:
        writer.writerows(rows)

# run with 5 threads
with ThreadPoolExecutor(max_workers=5) as executor:
    for idx, url in enumerate(urls, start=1):
        executor.submit(process_page, idx, url)

out_f.close()
print(f"Done — up to {total * 20} URLs written to {output_file}")