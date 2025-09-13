import csv
import sqlite3
import os

# File names
URLS_FILE = "P2 Pagination Urls.csv"
BLACKLIST_FILE = "P9 Kohls Black List.csv"
OUTPUT_FILE = "P3 Pagination Urls Post Blacklist.csv"

# Remove output if it already exists
if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

# Connect to in-memory SQLite and set up tables
conn = sqlite3.connect(":memory:")
c = conn.cursor()
c.execute("CREATE TABLE urls (url TEXT)")
c.execute("CREATE TABLE blacklist (url TEXT)")

# Helper to load a one-column CSV into a table, skipping a header if present
def load_table(csv_path, table_name):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        start = 0
        # If first row doesn’t start with “http”, treat it as a header
        if rows and not rows[0][0].lower().startswith("http"):
            header = rows[0][0]
            start = 1
        else:
            header = None
        for row in rows[start:]:
            url = row[0].strip()
            if url:
                c.execute(f"INSERT INTO {table_name} VALUES (?)", (url,))
        return header

# Load data
urls_header = load_table(URLS_FILE, "urls")
_ = load_table(BLACKLIST_FILE, "blacklist")
conn.commit()

# Count total and blacklisted
c.execute("SELECT COUNT(*) FROM urls")
total_urls = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM urls WHERE url IN (SELECT url FROM blacklist)")
deleted_count = c.fetchone()[0]

# Fetch only the non-blacklisted
c.execute("SELECT url FROM urls WHERE url NOT IN (SELECT url FROM blacklist)")
remaining = c.fetchall()

# Write the filtered URLs out
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if urls_header:
        writer.writerow([urls_header])
    for (url,) in remaining:
        writer.writerow([url])

print(f"{deleted_count} URLs were deleted due to the blacklist.")

conn.close()
