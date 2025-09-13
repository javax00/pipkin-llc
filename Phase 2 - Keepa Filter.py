import os
import pandas as pd
from datetime import datetime, timedelta

brands_to_remove = [
"Perfumes Club",
"Veronica Beard",
"Ugly Stik",
"New Era",
"Legion Athletics",
"Under Armour",
"Charles Tyrwhitt",
"Peter Thomas Roth",
"Murad",
"Kiehl’s",
"Gymshark",
"Birkenstock",
"Topo Designs",
"Tommy Hilfiger",
"Brooks Brother",
"Eddie Bauer",
"DSW",
"PrettyLittleThing",
"Betsey Johnson",
"The Children’s Place",
"Gymboree",
"GAP",
"Delonghi",
"Cafe Britt",
"Competitive Cyclist",
"Mielle Organics",
"Ahava",
"Lenox",
"Everything Kitchens",
"Blain's Farm & Fleet",
"Bealls Florida",
"Ninja KItchen",
"DK Hardware",
"Anker Solix",
"Lumens",
"Lenovo",
"Dell",
"Bose",
"Vesync",
"Arlo",
"Petlibro",
"Nanit",
"Love to dream",
"HALO",
"Maisonette",
"Mustela",
"Janie and Jack",
"Pool Parts to go",
"5.11 Tactical",
"Penhaligon’s",
"Academy",
"Public goods",
"Piping Rock",
"Acorn",
"Express",
"Arctic Fox",
"Vitamin Shoppe",
"Philosophy",
"Life Extensions"
]

# Find the first KeepaExport CSV file
candidates = [f for f in os.listdir('.') if 'KeepaExport' in f and f.lower().endswith('.csv')]
if not candidates:
    raise FileNotFoundError("No file with 'KeepaExport' found in the current directory.")
filename = candidates[0]
print(f"Opening: {filename}")

df = pd.read_csv(filename, dtype=str)

# --- Filter 1: Listed since is at least 6 months ago or older ---
# six_months_ago = datetime.now() - timedelta(days=182)
# parsed_date = pd.to_datetime(df['Listed since'], errors='coerce', format='%Y/%m/%d')
# if parsed_date.isna().all():
#     parsed_date = pd.to_datetime(df['Listed since'], errors='coerce', format='%d/%m/%Y')
# df = df[parsed_date <= six_months_ago]

# --- Filter 2: Sales Rank: Current < 300,000 ---
if 'Sales Rank: Current' in df.columns:
    bsr = pd.to_numeric(df['Sales Rank: Current'].astype(str).str.replace(',', ''), errors='coerce')
    df = df[bsr < 300000]

# --- Filter 3: Buy Box: % Amazon 90 days ≤ 60% ---
if 'Buy Box: % Amazon 90 days' in df.columns:
    buybox_pct = pd.to_numeric(df['Buy Box: % Amazon 90 days'].str.replace('%', ''), errors='coerce')
    df = df[buybox_pct <= 60]

# --- Filter 4: Remove rows with Brand in brands_to_remove ---
# if 'Brand' in df.columns:
#     df['Brand'] = df['Brand'].astype(str).str.strip()
#     brands_set = set([b.strip() for b in brands_to_remove])
#     df = df[~df['Brand'].isin(brands_set)]

# --- Delete the old KeepaExport file ---
os.remove(filename)
del filename

# --- Save result ---
df.to_csv('KeepaExport NEW.csv', index=False)
print(f"✅ Filtered file saved as 'KeepaExport NEW.csv' with {len(df)} rows.")
