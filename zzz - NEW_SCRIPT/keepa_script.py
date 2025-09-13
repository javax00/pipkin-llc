import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import math

# ---------------------------
# Load API key
# ---------------------------
load_dotenv()
API_KEY = os.getenv("KEEPA_API_KEY")
ASIN = "B088JDJ6MS"  # example ASIN

if not API_KEY:
    raise ValueError("❌ Missing Keepa API key. Add KEEPA_API_KEY=your_key in .env")

# ---------------------------
# Fetch Keepa API data
# ---------------------------
url = f"https://api.keepa.com/product?key={API_KEY}&domain=1&asin={ASIN}&stats=90&days=90"
response = requests.get(url)
data = response.json()

if "products" not in data or not data["products"]:
    raise ValueError("❌ No product data returned from Keepa API")

product = data["products"][0]
upc = product['upcList'][0]
csv = product["csv"]

# ---------------------------
# Helper to decode history arrays
# ---------------------------
EPOCH = datetime(2011, 1, 1, tzinfo=timezone.utc)

def convert_history(history, name, price=False):
    if not history:
        return pd.DataFrame(columns=["date", name])
    if len(history) % 2 != 0:
        history = history[:-1]
    times = [EPOCH + timedelta(minutes=history[i]) for i in range(0, len(history), 2)]
    values = [history[i] if history[i] != -1 else None for i in range(1, len(history), 2)]
    if price:  # cents → USD
        values = [v/100 if v is not None else None for v in values]
    return pd.DataFrame({"date": times, name: values})

# ---------------------------
# Sales Rank
# ---------------------------
sales_ranks = convert_history(csv[3], "salesRanks")

# ---------------------------
# Auto-detect New Offer Count
# ---------------------------
new_offer_count = pd.DataFrame(columns=["date", "NewOfferCount"])
for idx, arr in enumerate(csv):
    if arr and any(v not in (-1, None) for v in arr):
        sample_vals = [arr[j] for j in range(1, min(len(arr), 200), 2) if arr[j] != -1]
        if sample_vals and all(0 <= v <= 200 for v in sample_vals[:20]):
            new_offer_count = convert_history(csv[idx], "NewOfferCount")
            break

# ---------------------------
# Get List Price, fallback to New Price
# ---------------------------
list_price = pd.DataFrame(columns=["date", "ListPrice"])
if len(csv) > 16 and csv[16]:
    list_price = convert_history(csv[16], "ListPrice", price=True)

# If no List Price → fall back to New Price
if list_price.empty or list_price["ListPrice"].dropna().empty:
    list_price = convert_history(csv[1], "ListPrice", price=True)

# Monthly sold
monthly_sold = product.get("monthlySold", 0)

# ---------------------------
# Filter last 3 months
# ---------------------------
cutoff = datetime.now(timezone.utc) - timedelta(days=90)
df_sales = sales_ranks[sales_ranks["date"] >= cutoff]
df_offers = new_offer_count[new_offer_count["date"] >= cutoff]
df_price = list_price[list_price["date"] >= cutoff]

# ---------------------------
# Compute averages
# ---------------------------
avg_sales_rank  = df_sales["salesRanks"].mean()
avg_offer_count = df_offers["NewOfferCount"].mean()
avg_list_price  = df_price["ListPrice"].mean()

asr = math.floor(avg_sales_rank) if pd.notnull(avg_sales_rank) else 0
anoc = math.floor(avg_offer_count) if pd.notnull(avg_offer_count) else 0
alp = math.floor(avg_list_price) if pd.notnull(avg_list_price) else 0

# ---------------------------
# Print results
# ---------------------------
print(f"UPC              = {upc}")
print(f"avgSalesRanks    = {asr} {'OK' if asr <= 300000 else 'X'}")
print(f"avgNewOfferCount = {anoc} {"OK" if 15 <= anoc <= 20 else "X"}")
print(f"avgListPriceUSD  = {alp} {'OK' if alp >= 15 else 'X'}")
print(f"monthlySold      = {monthly_sold} {'OK' if monthly_sold >= 90 else 'X'}")
