import asyncio
import csv
import re

import requests
from dotenv import load_dotenv
from prisma import Prisma

from crawler.config import Config
from crawler.link import Link
from crawler.prismac import PrismaClient

load_dotenv()

# This script adds additional root URLs to the database work queue. Because they are initialized with
# depth 0 they will be prioritized


def parse_csv_to_dict_list(csv_file_path):
    rows = []  # Initialize an empty list to store rows as dictionaries

    with open(csv_file_path, 'r') as csv_file:
        # Use DictReader to automatically parse rows into dictionaries
        csv_reader = csv.DictReader(csv_file)

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

def add_aldaily_urls():
    li = []
    for page in range(1, 41):
        li.append(f"https://www.aldaily.com/essays-and-opinions/?page={page}")
    return li

def add_blogshn_urls():
    blog_directory = "https://raw.githubusercontent.com/surprisetalk/blogs.hn/main/blogs.json"
    response = requests.get(blog_directory)
    urls = response.json()
    return [x["url"] for x in urls]

def add_ooh_directory_urls():
    files = ["futures.xml", "humanities.xml", "personal.xml", "technology.xml", "society.xml", "history.xml", "language.xml", "economics.xml"]

    pattern = r'htmlUrl="([^"]*)"'
    urls = []
    for f in files:
        with open(f"/Users/henry/Downloads/{f}", "r") as file:
            text = file.read()
            html_urls = re.findall(pattern, text)
            urls += html_urls
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
    urls += add_aldaily_urls()
    urls += add_ooh_directory_urls()


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
