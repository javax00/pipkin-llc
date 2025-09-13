import os

# Define exact matches and partial matches
exact_matches = {"SU Cleaned", "Keepa Cleaned"}
partial_matches = ["KeepaExport", "ScanUnlimited"]

# Counter for how many files were deleted
deleted_count = 0

# Iterate through all files in the current directory
for filename in os.listdir():
    # Check if it's a CSV file
    if filename.endswith(".csv"):
        file_base = os.path.splitext(filename)[0]

        # Check for exact match (without extension)
        if file_base in exact_matches:
            os.remove(filename)
            print(f"Deleted: {filename}")
            deleted_count += 1
        # Check for partial match
        elif any(partial in file_base for partial in partial_matches):
            os.remove(filename)
            print(f"Deleted: {filename}")
            deleted_count += 1

print(f"\nTotal files deleted: {deleted_count}")
