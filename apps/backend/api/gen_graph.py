import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from tracemalloc import start

from api.main import D3Link, NodePage, PageNodesResponse
from crawler.prismac import PostgresClient, pg_client
from pydantic import BaseModel
from pydantic.json import pydantic_encoder

depth_to_search = 11
url_limit = -1


# Function to process a single URL synchronously and collect pages
def process_url_sync(pg_client, url, task_number):
    print(f'{task_number}: Processing {url}')
    pages = pg_client.get_network(url, depth_to_search)
    print(f'{task_number}: Finished processing {url}')
    return pages

# Asynchronous function to process a list of root URLs and create a single graph


async def process_root_urls_async(root_urls: list[str]):
    pg_client.connect()
    print('Starting query for multiple URLs')

    starting = pg_client.get_urls_by_depth(1)
    starting = starting[:url_limit]

    # blacklist = ['startups-emotionally-draining']
    starting = filter(
        lambda url: not 'startups-emotionally-draining' in url, starting)
    root_urls.extend(starting)

    adjacency_list = {}
    all_pages = []

    # Run synchronous tasks concurrently using a thread pool - TODO: each thread needs its own connection
    # with ThreadPoolExecutor() as executor:
    #     loop = asyncio.get_running_loop()
    #     tasks = [loop.run_in_executor(
    #         executor, process_url_sync, pg_client, url, i+1) for i, url in enumerate(root_urls)]

    #     for completed_task in asyncio.as_completed(tasks):
    #         pages = await completed_task
    #         all_pages.extend(pages)
    #         adjacency_list.update({p.url: p for p in pages})
    #         print(f"Done with {len(all_pages)} pages")
    #     print(f'Finished processing {len(all_pages)} pages')

    # Synchronously:
    count = 0
    for root_url in root_urls:
        print(f'{count} Processing {root_url}')
        pages = pg_client.get_network(root_url, depth_to_search)
        all_pages.extend(pages)
        adjacency_list.update({p.url: p for p in pages})
        count += 1

    links: list[D3Link] = []

    print('Creating links')

    # Create links for the entire graph
    for neighbor in adjacency_list.values():
        print(f"Creating links for {neighbor.url}")
        for outbound_link in neighbor.outbound_urls:
            if outbound_link in adjacency_list:
                link = D3Link(source=neighbor.url, target=outbound_link)
                links.append(link)

    nodes = list(adjacency_list.values())

    precomputed_global_graph = PageNodesResponse(
        nodes=nodes, links=links, root_url="multiple_urls")

    # Write to file 'graph.json'
    file_path = '../web/public/graph_multiple_urls.json'
    with open(file_path, 'w') as f:
        f.write(precomputed_global_graph.json())
    print(f"Combined graph written to {file_path}")

# Example usage with an array of root URLs
root_urls = [
    "https://hypertext.joodaloop.com/",
    'https://macwright.com/2020/05/10/spa-fatigue.html',
    'https://eriktorenberg.substack.com/p/reconsidering-career-optionality?s=r',
    'https://vitalik.ca/general/2021/08/16/voting3.html',
    # "https://simonwillison.net/2023/Mar/13/alpaca"
]

# Run the asynchronous function
asyncio.run(process_root_urls_async(root_urls))
