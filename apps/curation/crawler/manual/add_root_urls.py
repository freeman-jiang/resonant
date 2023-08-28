import asyncio
import csv
import re

from prisma import Prisma

from crawler.config import Config
from crawler.link import Link
from crawler.prisma import PrismaClient

# This script adds additional root URLs to the database work queue. Because they are initialized with
# depth 0 they will be prioritized
def parse_csv_to_dict_list(csv_file_path):
    rows = []  # Initialize an empty list to store rows as dictionaries

    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)  # Use DictReader to automatically parse rows into dictionaries

        for row in csv_reader:
            rows.append(row)  # Append each row dictionary to the list

    return rows

def extract_url_from_text(html_text):
    # Define a regular expression pattern to match the href attribute
    href_pattern = r'<a\s+href="([^"]+)"'

    # Search for the href attribute using the pattern
    match = re.search(href_pattern, html_text)

    if match:
        href_attribute = match.group(1)
        return href_attribute
    else:
        print("No href attribute found.", html_text)

def add_dm_hn_urls():
    # Parse CSV file at dm_hn_data.csv
    # For each row, add the URL to the database
    data = parse_csv_to_dict_list("crawler/manual/dm_hn_data.csv")

    urls = [extract_url_from_text(row["Description"]) for row in data]
    urls = list(filter(lambda url: url is not None, urls))

    print(urls)
    return urls


async def main():
    config = Config()
    db = Prisma()
    await db.connect()
    pc = PrismaClient(config, db)

    urls = []
    # with open("crawler/ROOT_URLS.txt", "r") as f:
    #     urls = f.readlines()

    urls += add_dm_hn_urls()

    links = []

    for url in urls:
        try:
            link = Link.from_url(url)
        except ValueError:
            print("Invalid URL: ", url)
            continue
        links.append(link)
    tasks_created = await pc.add_tasks(links)

    print(
        f"Added {tasks_created} new tasks to the work queue")

    await db.disconnect()

if __name__ == "__main__":
    # add_dm_hn_urls()
    asyncio.run(main())
