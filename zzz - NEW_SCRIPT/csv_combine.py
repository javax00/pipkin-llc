import pandas as pd
import glob
import os

# Find all CSV files that start with "KeepaExport"
csv_files = glob.glob("KeepaExport*.csv")

if not csv_files:
    print("No CSV files found starting with 'KeepaExport'")
else:
    all_dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            df["source_file"] = os.path.basename(file)  # optional: track source
            all_dfs.append(df)
            print(f"Loaded: {file} ({len(df)} rows)")
        except Exception as e:
            print(f"Error reading {file}: {e}")

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        output_file = "KeepaExport-ALL.csv"
        combined.to_csv(output_file, index=False)
        print(f"\n✅ Combined CSV saved as '{output_file}' with {len(combined)} rows")

        # Delete original files
        for file in csv_files:
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")
    else:
        print("No dataframes were created. Nothing to save.")
