import os
import json

# Get the path to product.json in the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(script_dir, 'product.json')

if not os.path.exists(json_file):
    print(f"File not found: {json_file}")
    exit()

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Pretty-print the entire JSON
# print(json.dumps(data, indent=2, ensure_ascii=False))

colors = 'Collegiate Navy_River Blue_Mountain Red'.split('_')
ids = '473'

for color in colors:
    for x in data['product']['variationAttributes'][0]['values']:
        if x['displayValue'] == color:
            if x['selectable'] == True and x['masterSelectable'] == True:
                # print(x['id'])
                # print(x['displayValue'])
                # print(x['salesPrice']['value'])

                for y in data['product']['variantData']:
                    if data['product']['variantData'][y]['color'] == x['id']:
                        # print('  - '+[y][0])
                        # print('  - '+data['product']['variantData'][y]['color'])
                        # print('  - '+data['product']['variantData'][y]['size'])
                        # print()

                        print('UPC: '+[y][0])
                        print('Price: '+str(x['salesPrice']['value']))
                        print('Variant: '+x['displayValue']+' - '+data['product']['variantData'][y]['size'])
                        print('Source Link: '+x['url'])
                        print('')

