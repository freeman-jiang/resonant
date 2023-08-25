from collections import defaultdict

from pydantic import BaseModel

from crawler.database import Database
from crawler.link import get_domain
from crawler.parse import CrawlResult




class Node(BaseModel):
    out: list[str]
    url: str

def pagerank(graph: dict[str, Node], damping_factor=0.99, max_iterations=9, tolerance=1e-6):
    num_nodes = len(graph)
    initial_value = 1.0 / num_nodes

    # Initialize PageRank values
    pagerank_values = {url: 0 for url in graph}
    pagerank_values["https://danluu.com/hiring-lemons"] = 1.0
    new_pagerank_values = pagerank_values.copy()

    for _ in range(max_iterations):
        total_diff = 0.0
        for node_url, node in graph.items():
            if len(node.out) == 0:
                used_damping = 0
            else:
                used_damping = damping_factor
            share = pagerank_values[node_url] / (max(len(node.out), 1))
            for neighbor_url in node.out:
                new_pagerank_values[neighbor_url] += used_damping * share
            # Add random jump
            random_jump_value = (1 - used_damping) * initial_value
            new_pagerank_values[node_url] += random_jump_value

            total_diff += abs(new_pagerank_values[node_url] - pagerank_values[node_url])

        pagerank_values = new_pagerank_values.copy()


        [print(k, v) for k, v in pagerank_values.items() if v > 0.025]
        new_pagerank_values = {url: initial_value for url in graph}

        if total_diff < tolerance:
            break

    return pagerank_values
def load_from_db():
    db = Database(CrawlResult, "my_database")
    graph = {}

    for _key, value in db.items():
        result = value

        links = [x.url for x in result.outgoing_links]

        # links = filter(lambda k: get_domain(k) != get_domain(result.link.url), links)
        node = Node(out=links, url=result.link.url)
        graph[result.link.url] = node
    for node in graph.values():
        node.out = list(filter(lambda k: k in graph, node.out))

    most_connected = defaultdict(int)

    for node in graph.values():
        for url in node.out:
            print(f"{node.url} -> {url}")
            most_connected[url] += 1

    most_connected = most_connected.items()
    most_connected = sorted(pagerank(graph).items(), key=lambda k: k[1], reverse=True)
    print(most_connected)
    # print(pagerank(graph))


if __name__ == "__main__":
    load_from_db()
