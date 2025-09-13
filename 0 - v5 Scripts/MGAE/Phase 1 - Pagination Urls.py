import csv

def main():
    # Prompt the user for how many pages to generate
    total_pages = int(input("Enter total number of pages: ").strip())

    # Base URL (page 1)
    base_url = "https://shop.mgae.com/collections/all-1"

    # Prepare list of links
    links = []
    for page in range(1, total_pages + 1):
        if page == 1:
            links.append([base_url])
        else:
            links.append([f"{base_url}?page={page}"])

    # Write to CSV file
    with open("P1 Pagination Links.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL"])
        writer.writerows(links)

    print(f"\n✅ {total_pages} links saved to 'P1 Pagination Links.csv'.")

if __name__ == "__main__":
    main()
