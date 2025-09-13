import os
import sys
import pandas as pd
import numpy as np

# 1) Auto-detect “KeepaExport” file
candidates = [f for f in os.listdir('.') if 'KeepaExport' in f]
if not candidates:
    print("No file with 'KeepaExport' found in the current directory.")
    sys.exit(1)
keepa_file = candidates[0]
_, ext = os.path.splitext(keepa_file.lower())

# 2) Excel check → blank CSV
if ext in ('.xls', '.xlsx'):
    print("File format is excel, CSV expected. Please upload CSV file.")
    open("Keepa Cleaned.csv", "w").close()
    sys.exit(0)
if ext != '.csv':
    print(f"Unrecognized extension '{ext}'. Expected .csv")
    sys.exit(1)

# 3) Load Keepa CSV
df = pd.read_csv(keepa_file, dtype=str)
df.columns = df.columns.str.strip()
df.replace('-', '', inplace=True)

# 4) Keep only the allowed Keepa columns
keepa_allowed = [
    "Title", "ASIN", "New: Current",
    "Buy Box 🚚: Current", "Buy Box 🚚: 30 days avg.", "Buy Box 🚚: 90 days avg.",
    "Reviews: Rating Count - Format Specific", "Reviews: Rating Count",
    "New Offer Count: Current", "Bought in past month",
    "Sales Rank: Current", "Amazon: Current", "Amazon: 90 days OOS",
    "FBA Pick&Pack Fee", "Referral Fee %", "Competitive Price Threshold",
    "Return Rate"
]
df = df[[c for c in keepa_allowed if c in df.columns]]

# 5) Rename columns
rename_map = {
    "New: Current": "New",
    "Buy Box 🚚: Current": "BB",
    "Buy Box 🚚: 30 days avg.": "BB 30",
    "Buy Box 🚚: 90 days avg.": "BB 90",
    "Reviews: Rating Count - Format Specific": "Rating",
    "Reviews: Rating Count": "T Rating",
    "New Offer Count: Current": "Offer",
    "Bought in past month": "# Sold",
    "Sales Rank: Current": "Rank",
    "Amazon: Current": "Amz",
    "Amazon: 90 days OOS": "Amz OOS",
    "FBA Pick&Pack Fee": "FBA Fee",
    "Referral Fee %": "Ref Fee",
    "Competitive Price Threshold": "CPT",
    "Return Rate": "Return"
}
df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns},
          inplace=True)

# 6) Clean up numeric strings
for col in ['FBA Fee', 'New', 'BB', 'BB 30', 'BB 90', 'CPT']:
    if col in df.columns:
        df[col] = df[col].replace(r'[\$,]', '', regex=True)

# 7) Convert to numeric for filtering
fba   = pd.to_numeric(df.get('FBA Fee', pd.Series()), errors='coerce')
ref   = pd.to_numeric(df.get('Ref Fee', pd.Series()).str.rstrip('%'), errors='coerce') / 100
offer = pd.to_numeric(df.get('Offer', pd.Series()), errors='coerce')

# 8) Drop rows where FBA Fee, Ref Fee, or Offer is missing or ≤0
mask = (fba.fillna(0) > 0) & (ref.fillna(0) > 0) & (offer.fillna(0) > 0)
df = df.loc[mask].copy()

# 9) Round Ref Fee to whole percent
df['Ref Fee'] = (ref[mask] * 100).round(0).astype(int).astype(str).add('%')

# 10) Format large counts
for col in ['Rating', 'T Rating', 'Rank']:
    if col in df.columns:
        df[col] = (
            pd.to_numeric(df[col], errors='coerce')
              .fillna(0)
              .astype(int)
              .map(lambda x: f"{x:,}")
        )
if '# Sold' in df.columns:
    df['# Sold'] = (
        pd.to_numeric(df['# Sold'], errors='coerce')
          .fillna(0)
          .astype(int)
          .map(lambda x: f"{x:,}" if x != 0 else '')
    )

# 11) Merge in SU Cleaned.csv
su_file = "SU Cleaned.csv"
if os.path.exists(su_file):
    su = pd.read_csv(su_file, dtype=str)
    su.columns = su.columns.str.strip()
    for drop in ('Profit', 'ROI'):
        if drop in su.columns:
            su.drop(columns=drop, inplace=True)
    if 'ASIN' in su.columns:
        su_cols = [c for c in su.columns if c != 'ASIN']
        df = df.merge(su[['ASIN'] + su_cols], on='ASIN', how='left')
        print(f"Merged SU data: {', '.join(su_cols)}")
    else:
        print(f"Warning: '{su_file}' missing ASIN; skipped merge.")
else:
    print(f"SU file '{su_file}' not found; skipped merge.")

# 12) Prepare numeric series for calculations
num_BB      = pd.to_numeric(df.get('BB', pd.Series()), errors='coerce')
num_New     = pd.to_numeric(df.get('New', pd.Series()), errors='coerce')
num_BB30    = pd.to_numeric(df.get('BB 30', pd.Series()), errors='coerce')
num_BB90    = pd.to_numeric(df.get('BB 90', pd.Series()), errors='coerce')
num_CPT     = pd.to_numeric(df.get('CPT', pd.Series()), errors='coerce')
num_Cost    = pd.to_numeric(df.get('Cost', pd.Series()).replace(r'[\$,]', '', regex=True), errors='coerce')
num_FBA     = fba
num_RefPct  = ref
num_Rating  = pd.to_numeric(df.get('Rating', pd.Series()).str.replace(',', ''), errors='coerce')
num_TRating = pd.to_numeric(df.get('T Rating', pd.Series()).str.replace(',', ''), errors='coerce')

# 13) Calculations
list_val    = num_BB.fillna(num_New)
profit_val  = list_val - num_Cost - num_FBA - (num_RefPct * list_val)
roi_val     = profit_val / num_Cost
bb3090      = pd.concat([num_BB30, num_BB90], axis=1).min(axis=1, skipna=True)
p3090       = bb3090 - num_Cost - num_FBA - (num_RefPct * bb3090)
pct         = num_Rating / num_TRating
cpt_profit  = num_CPT - num_Cost - num_FBA - (num_RefPct * num_CPT)
cpt_roi     = cpt_profit / num_Cost

df['List']        = list_val.map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
df['Profit']      = profit_val.map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
df['ROI']         = roi_val.map(lambda x: f"{x*100:.0f}%" if pd.notna(x) and np.isfinite(x) else "")
df['30/90 BB']    = bb3090.map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
df['30/90 Profit']= p3090.map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
df['%']           = pct.map(lambda x: f"{x*100:.0f}%" if pd.notna(x) and np.isfinite(x) else "")
df['BB/SUP']      = np.where(num_BB.fillna(0) > 0, 'BB', 'SUP')
df['CPT Profit']  = cpt_profit.map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
df['CPT ROI']     = cpt_roi.map(lambda x: f"{x*100:.0f}%" if pd.notna(x) and np.isfinite(x) else "")
df['Amazon']      = df['ASIN'].map(lambda x: f"https://www.amazon.com/dp/{x}?th=1&psc=1")

# 14) Drop intermediate columns no longer needed
df.drop(columns=[c for c in ['New','BB','BB 30','BB 90','FBA Fee','Ref Fee'] if c in df.columns],
        inplace=True)

# 15) Filter out ROI < 10%
df['ROI_numeric'] = pd.to_numeric(df['ROI'].str.rstrip('%'), errors='coerce') / 100
df = df[df['ROI_numeric'] >= 0.10].copy()
df.drop(columns=['ROI_numeric'], inplace=True)

# 16) Sort by # Sold (desc), then Rating (desc)
df['# Sold Sort']   = pd.to_numeric(df['# Sold'].str.replace(',', ''), errors='coerce').fillna(0)
df['Rating Sort']   = pd.to_numeric(df['Rating'].str.replace(',', ''), errors='coerce').fillna(0)
df.sort_values(by=['# Sold Sort','Rating Sort'], ascending=[False,False], inplace=True)
df.drop(columns=['# Sold Sort','Rating Sort'], inplace=True)

# 17) Format Cost as currency with two decimals
df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce')\
               .map(lambda x: f"${x:,.2f}" if pd.notna(x) else "")

# 18) Reorder columns dynamically
standard_order = [
    "ASIN","Title","Cost","List","Profit","ROI",
    "Offer","Rank","# Sold","30/90 BB","30/90 Profit",
    "Rating","T Rating","%","Return","BB/SUP",
    "CPT","CPT Profit","CPT ROI","Amz","Amz OOS"
]
std_existing = [c for c in standard_order if c in df.columns]
custom       = [c for c in df.columns if c not in std_existing + ["Source","Amazon"]]
final_order  = std_existing + custom + ["Source","Amazon"]
df = df[final_order]

# 19) Save final CSV
df.to_csv("Keepa Cleaned.csv", index=False)
print(f"✅ Done: 'Keepa Cleaned.csv' with {len(df)} rows & {len(df.columns)} columns.")