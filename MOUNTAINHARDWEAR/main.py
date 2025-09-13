import undetected_chromedriver as uc
import time
import os
import csv

url = "https://www.mountainhardwear.com/c/summer-sale-main/?pmid=dynamic-category-promotion-sale&all=true"

options = uc.ChromeOptions()
options.headless = False
options.add_argument("--disable-blink-features=AutomationControlled")
driver = uc.Chrome(options=options)

def close_popups(driver):
    try:
        btn = driver.find_element("css selector", ".onetrust-close-btn-handler")
        btn.click()
        time.sleep(0.5)
    except Exception:
        pass
    try:
        btn = driver.find_element("css selector", "div.js-action__closeoverlay")
        btn.click()
        time.sleep(0.5)
    except Exception:
        pass

driver.get(url)
time.sleep(5)
close_popups(driver)

prev_height = driver.execute_script("return document.body.scrollHeight")
unchanged = 0
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    curr_height = driver.execute_script("return document.body.scrollHeight")
    if curr_height == prev_height:
        unchanged += 1
        if unchanged >= 3:
            break
    else:
        unchanged = 0
    prev_height = curr_height

print("Reached bottom, waiting 3 seconds...")
time.sleep(3)

products = driver.find_elements("css selector", 'div.product')
rows = []

count = 1
for product in products:
    print(f"Processing product {count}/{len(products)}")
    try:
        data_pid = product.get_attribute('data-pid')
        color_names = []

        swatch_wrapper = product.find_element("css selector", 'div.swiper-container--swatches')
        swatches = swatch_wrapper.find_elements("css selector", 'a.js-color-swatch')

        for swatch in swatches:
            try:
                # Get color name from span.swatch__core (use title if exists, else text)
                span = swatch.find_element("css selector", "span.swatch__core")
                color_name = span.get_attribute("title") or span.text
                color_name = color_name.strip()
                if color_name and color_name not in color_names:
                    color_names.append(color_name)
            except Exception:
                continue

        if data_pid and color_names:
            url_str = f'https://www.mountainhardwear.com/on/demandware.store/Sites-MountainHardwear_US-Site/en_US/Product-Variation?pid={data_pid}'
            rows.append(['_'.join(color_names), url_str])
        count += 1
    except Exception as e:
        print(f"Error scraping product: {e}")

print(f"Total products found: {len(products)}")

# Save to CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(script_dir, 'product_url.csv')

if os.path.exists(csv_file):
    os.remove(csv_file)
    print(f"Deleted existing file: {csv_file}")

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Color', 'URL'])
    writer.writerows(rows)
print(f"Saved to {csv_file}")

driver.quit()