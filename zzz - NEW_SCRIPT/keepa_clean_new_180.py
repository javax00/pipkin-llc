import pandas as pd
import glob
import csv  # for quoting

# Find CSV file(s) with "KeepaExport" in the name
files = glob.glob("KeepaExport*.csv")

if not files:
    raise FileNotFoundError("No CSV file with 'KeepaExport' in the name found.")

# Load the first matching CSV
df = pd.read_csv(files[0])

# --- Price column ---
df["Price"] = df["List Price: 180 days avg."].fillna(df["New: 180 days avg."])
df["Price"] = (
    df["Price"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.strip()
)
df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0.0)

# --- Buy Box column ---
df["Buy Box 🚚: 180 days avg."] = (
    df["Buy Box 🚚: 180 days avg."]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.strip()
)

# --- Bought in past month ---
df["Bought in past month"] = pd.to_numeric(
    df["Bought in past month"], errors="coerce"
).fillna(0).astype(int)

# --- Apply filters ---
filtered = df[
    (df["Sales Rank: 180 days avg."] < 300000) &
    (df["Price"] >= 15) &
    (df["New Offer Count: 180 days avg."].between(15, 20)) &
    (df["Bought in past month"] >= 30)
]

# --- Rename columns ---
filtered = filtered.rename(columns={
    "Product Codes: UPC": "UPC",
    "Title": "Title",
    "ASIN": "ASIN",
    "Sales Rank: 180 days avg.": "Sales Rank 180",
    "Price": "Price 180",
    "New Offer Count: 180 days avg.": "New Count Offer 180",
    "Bought in past month": "Monthly Sold",
    "Buy Box 🚚: 180 days avg.": "Buy Box 180"
})

# --- Clean UPC ---
filtered["UPC"] = (
    filtered["UPC"]
    .astype(str)
    .str.strip()
    .str.split(",")      # keep only first UPC if multiple
    .str[0]
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)  # remove trailing .0
)

# Drop invalid UPCs
filtered = filtered[~filtered["UPC"].isin(["", "nan", "None", "NaN"])]

# --- Reorder columns ---
final_cols = [
    "UPC", "Title", "ASIN", "Sales Rank 180",
    "Price 180", "New Count Offer 180", "Monthly Sold", "Buy Box 180"
]
filtered = filtered[final_cols]

# --- Save ---
filtered.to_csv(
    "KeepaExport-CLEAN.csv",
    index=False,
    quoting=csv.QUOTE_ALL
)

print("✅ Saved filtered data with cleaned UPCs (first only) to KeepaExport-CLEAN.csv")
