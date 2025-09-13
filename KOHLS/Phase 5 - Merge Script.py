import pandas as pd
import os
from datetime import datetime

date_now = str(datetime.now().strftime("%m_%d_%Y"))

# ─── Configuration ────────────────────────────────────────────────────────────
file1      = "P3 UPCs.csv"
file2      = "P4 Add to Cart Checked.csv"
output_csv = "final_kohls_" + date_now + ".csv"

# ─── 1) Delete existing output (so we overwrite cleanly) ──────────────────────
if os.path.exists(output_csv):
    os.remove(output_csv)

# ─── 2) Load both CSVs as strings (preserve leading apostrophes, etc.) ────────
df1 = pd.read_csv(file1, dtype=str)
df2 = pd.read_csv(file2, dtype=str)

# ─── 3) Combine them end-to-end ───────────────────────────────────────────────
df = pd.concat([df1, df2], ignore_index=True)

# ─── 4) Drop the SkuCode column ──────────────────────────────────────────────
df = df.drop(columns=["SkuCode"], errors="ignore")

# ─── 5) Remove out-of-stock rows (Quantity blank or zero) ────────────────────
before = len(df)
# strip whitespace, convert to numeric (non-numbers→NaN→0), then keep only >0
qty = pd.to_numeric(df["Quantity"].str.strip(), errors="coerce").fillna(0)
df = df[qty > 0]
deleted = before - len(df)
print(f"Deleted {deleted} rows due to out of stock (Quantity blank or zero)")

# ─── 6) Remove any duplicate rows ────────────────────────────────────────────
df = df.drop_duplicates()

# ─── 7) Format Price as currency to two decimal places ───────────────────────
# convert to numeric, then map to strings like "$60.00"
df["Price"] = (
    pd.to_numeric(df["Price"], errors="coerce")
      .fillna(0)
      .map(lambda x: f"${x:,.2f}")
)

# ─── 8) Write out the cleaned, combined CSV ─────────────────────────────────
df.to_csv(output_csv, index=False)
print(f"Wrote {len(df)} rows to {output_csv!r}")
