# pip install requests
import requests
import csv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def generate_pagination_links(input_link, apikey, headers):
    # 1) Fetch the total number of pages
    params = {
        'url': input_link,
        'apikey': apikey,
        'custom_headers': 'true',
    }
    resp = requests.get('https://api.zenrows.com/v1/', params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    total_pages = data.get('pages', {}).get('totalPages')
    if total_pages is None:
        raise ValueError("Error: 'totalPages' not found in response.")

    # 2) Parse the input URL and remove existing anchor/count
    parsed = urlparse(input_link)
    base_qs = parse_qs(parsed.query)
    base_qs.pop('anchor', None)
    base_qs.pop('count', None)

    # 3) Build list of all page URLs
    links = []
    for i in range(total_pages):
        anchor = i * 24
        qs = { k: v[0] for k, v in base_qs.items() }
        qs.update({'anchor': str(anchor), 'count': '24'})
        new_query = urlencode(qs)
        page_url = urlunparse(parsed._replace(query=new_query))
        links.append(page_url)

    return links

if __name__ == '__main__':
    input_link = (
        'https://api.nike.com/discover/product_wall/v1/'
        'marketplace/US/language/en/consumerChannelId/'
        'd9a5bc42-4b9c-4976-858a-f159cf99c647'
        '?path=/w&queryType=PRODUCTS&anchor=0&count=24'
    )
    apikey = 'c55c9698146c8f7e3fa51276a74974890e5d56ec'
    headers = {
        'nike-api-caller-id': 'nike:dotcom:browse:wall.client:2.0',
    }

    # Generate the links
    all_links = generate_pagination_links(input_link, apikey, headers)

    # Write to CSV (no header), overwrite if exists
    output_file = 'P1 Pagination Urls.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for link in all_links:
            writer.writerow([link])

    # Print total count
    print(f"Wrote {len(all_links)} URLs to '{output_file}'")