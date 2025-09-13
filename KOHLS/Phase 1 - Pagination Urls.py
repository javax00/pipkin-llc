import math
import csv


def main():
    # Prompt for the starting link (may include existing modifiers)
    raw_url = input(
        "Enter starting link (e.g. https://www.kohls.com/catalog/nike.jsp?CN=Brand:Nike&PPP=48&WS=48): ").strip()

    # Clean up: remove everything from the first '&' onward (including the '&')
    base_url = raw_url.split("&", 1)[0]

    # Prompt for total number of products
    while True:
        try:
            total_products = int(input("Enter number of products (e.g. 14838): ").strip())
            if total_products < 0:
                raise ValueError
            break
        except ValueError:
            print("⚠️  Please enter a valid non-negative integer for the number of products.")

    per_page = 96
    total_pages = math.ceil(total_products / per_page)

    output_file = "P1 Pagination.csv"

    # Write pagination links to CSV (no header, overwrite if exists)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for page_index in range(total_pages):
            offset = page_index * per_page
            link = f"{base_url}&PPP={per_page}&WS={offset}"
            writer.writerow([link])

    print(f"\n✅ Wrote {total_pages} pagination link{'s' if total_pages != 1 else ''} to {output_file}")


if __name__ == "__main__":
    main()