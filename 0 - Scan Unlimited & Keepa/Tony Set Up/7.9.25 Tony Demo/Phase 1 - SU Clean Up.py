import os
import pandas as pd

# 1. Auto-detect the file containing "ScanUnlimited" in the script's directory
def find_input_file():
    candidates = [f for f in os.listdir() if "ScanUnlimited" in f and f.lower().endswith(('.csv', '.xls', '.xlsx'))]
    if not candidates:
        raise FileNotFoundError("No file containing 'ScanUnlimited' found in directory.")
    return candidates[0]

input_file = find_input_file()
print(f"Loading file: {input_file}")

# 2. Load the file into a DataFrame (CSV or Excel)
if input_file.lower().endswith('.csv'):
    df = pd.read_csv(input_file, dtype=str)
else:
    df = pd.read_excel(input_file, dtype=str)

# 3. Drop unwanted columns if they exist
cols_to_delete = [
    "UPC", "Sales Rank", "Title", "Variation Parent", "Price", "Size", "Color",
    "Estimated Sales", "Offers", "Average90", "Average180", "Package Quantity",
    "Review Count", "Review Stars", "Category", "Package Height", "Package Length",
    "Package Width", "Package Weight", "Amazon Last Seen", "FBA Fee", "Referral Fee",
    "Closing Fee", "Fixed Additional Cost", "Shipping Cost", "Percent Additional Cost",
    "Margin", "Brand", "Variations", "Average30"
]
for col in cols_to_delete:
    if col in df.columns:
        df.drop(columns=col, inplace=True)

# 4. Detect and rename the Source column (any column with URLs)
source_col = None
for col in df.columns:
    if df[col].astype(str).str.contains(r'https?://|www\.|\.com', na=False).any():
        source_col = col
        break
if source_col:
    df.rename(columns={source_col: 'Source'}, inplace=True)
    print(f"Renamed column '{source_col}' to 'Source'.")
else:
    print("No URL-containing column found to rename to 'Source'.")

# 5. Drop rows based on ROI between -95% and -2%
if 'ROI' in df.columns:
    # Convert 'ROI' from percentage string to numeric float
    df['ROI_numeric'] = pd.to_numeric(df['ROI'].str.rstrip('%'), errors='coerce')
    # Keep only rows NOT in the [-95, -2] range
    df = df[~((df['ROI_numeric'] >= -95) & (df['ROI_numeric'] <= -2))]
    # Remove helper column
    df.drop(columns='ROI_numeric', inplace=True)

# 6. Ensure required columns exist and order them
required = ['ASIN', 'Cost', 'Profit', 'ROI']
for col in required:
    if col not in df.columns:
        df[col] = ''  # create empty column if missing

# Build final column order: required first, then any other, then Source last
other_cols = [c for c in df.columns if c not in required + ['Source']]
final_order = required + other_cols
if 'Source' in df.columns:
    final_order.append('Source')

df = df[final_order]

# 7. Save output
output_file = "SU Cleaned.csv"
df.to_csv(output_file, index=False)
print(f"Saved cleaned file as: {output_file}")

# 8. Copy ASIN column to the Windows clipboard and report count
if 'ASIN' in df.columns:
    asin_series = df['ASIN'].dropna()
    # Copy to clipboard (one ASIN per line)
    asin_series.to_clipboard(index=False, header=False)
    count = len(asin_series)
    print(f"{count} ASINs copied to the clipboard")
else:
    print("No ASIN column found to copy to clipboard.")
