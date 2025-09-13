import pandas as pd

# 1) Load your two CSVs
df_urls = pd.read_csv('P2 Pagination Urls.csv')
df_upcs = pd.read_csv('P3 UPCs.csv')

# 2) Merge on productCode (keep all rows from P3 UPCs)
df = pd.merge(
    df_upcs,
    df_urls[['productCode', 'currentPrice', 'url', 'title', 'promotionId']],
    on='productCode',
    how='left'
)

# 3) Drop the now-unneeded isAvailable column
df = df.drop(columns=['isAvailable'])

# 4) Rename headers
df = df.rename(columns={
    'GTIN':        'UPC',
    'productCode': 'Model',
    'currentPrice':'Price',
    'url':         'Source',
    'title':       'Promo',
    'promotionId': 'Promo ID'
})

# 5) Remove rows with missing/empty Source
mask_missing = df['Source'].isna() | (df['Source'].astype(str).str.strip() == '')
removed_count = mask_missing.sum()
df = df[~mask_missing]
print(f'Removed {removed_count} rows due to missing Source URL')

# 6) Calculate ADJ column
def calc_adj(row):
    # Only for the special “See Price in Bag” promo
    if row['Promo'] == 'See Price in Bag':
        pid = str(row['Promo ID'])
        # first two chars → discount percent
        if pid[:2].isdigit():
            discount = int(pid[:2]) / 100.0
            return row['Price'] * (1 - discount)
    # default: no discount
    return row['Price']

# Insert ADJ right after Price
df.insert(
    loc=df.columns.get_loc('Price') + 1,
    column='ADJ',
    value=df.apply(calc_adj, axis=1)
)

# 7) Reorder to your desired layout
df = df[[
    'groupKey',
    'UPC',
    'Model',
    'ship',
    'Price',
    'ADJ',
    'Source',
    'Promo',
    'Promo ID'
]]

# 8) Write out (overwrites if it exists)
output_file = 'P4 Nike Stock Promo Source.csv'
df.to_csv(output_file, index=False)

print(f'✅ Written merged file to {output_file}')