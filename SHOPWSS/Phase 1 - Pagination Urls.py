# pip install requests
import math
import requests
import csv

# 1. Configuration
ZENROWS_API_URL = 'https://api.zenrows.com/v1/'
INITIAL_URL = (
    'https://searchserverapi1.com/getresults'
    '?api_key=4j0m7P2d3d'
    '&q='
    '&sortBy=collection_153378455607_position'
    '&sortOrder=desc'
    '&startIndex=0'
    '&maxResults=48'
    # PROMO PARAMS
    '&collection=on-sale'
)

ZENROWS_APIKEY = 'ef95565cee4ff7e6df2a9caa8f503da7b988ac2e'
OUTPUT_CSV = 'P1 Pagination Urls.csv'  # will overwrite if exists

def main():
    try:
        # 2. Fetch initial page
        # resp = requests.get(
        #     ZENROWS_API_URL,
        #     params={'url': INITIAL_URL, 'apikey': ZENROWS_APIKEY},
        #     timeout=30
        # )
        resp = requests.get(INITIAL_URL, timeout=90)

        resp.raise_for_status()
        data = resp.json()

        # 3. Extract pagination info
        total_items = data.get('totalItems')
        items_per_page = data.get('itemsPerPage')
        if not (isinstance(total_items, int) and isinstance(items_per_page, int)):
            raise ValueError('Missing totalItems or itemsPerPage in response')

        # 4. Calculate pages (round up)
        num_pages = math.ceil(total_items / items_per_page)

        # 5. Build base URL
        base_url = INITIAL_URL.split('&startIndex=')[0].split('&maxResults=')[0]

        # 6. Write all pagination links to CSV (no headers)
        with open(OUTPUT_CSV, 'w', newline='') as f:
            writer = csv.writer(f)
            for page in range(num_pages):
                start_index = page * items_per_page
                link = (
                    f'{base_url}'
                    f'&startIndex={start_index}'
                    f'&maxResults={items_per_page}'
                )
                writer.writerow([link])

    except Exception:
        # On any error, overwrite with a blank file
        with open(OUTPUT_CSV, 'w', newline='') as f:
            pass

if __name__ == '__main__':
    main()
