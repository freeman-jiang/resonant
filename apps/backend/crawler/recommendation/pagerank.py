import json
from collections import defaultdict

from psycopg import Connection
from psycopg.rows import kwargs_row

from crawler.dbaccess import db

from dotenv import load_dotenv

from crawler.recommendation.nodes import PageAsNode, Node, url_to_domain

load_dotenv()


def top_domains(trustrank_values: dict) -> dict[str, float]:
    trustrank_values_sorted = sorted(
        [(k, v) for k, v in trustrank_values.items()], key=lambda k: k[1])
    return trustrank_values_sorted


NORMAL_ADDS = defaultdict(int)


def add_rank(d, url, value):
    d[url] += value


def trustrank(graph: dict[str, Node], damping_factor=0.90, max_iterations=100, tolerance=1.0) -> dict[str, float]:
    trusted_nodes = [(url, node.individual_pages)
                     for url, node in graph.items() if node.best_depth <= 1]
    trusted_nodes_len = sum(
        x.individual_pages for x in graph.values() if x.best_depth <= 1)

    # Initialize TrustRank values
    trustrank_values = {url: node.score for url, node in graph.items()}
    initial_values = {url: 0 for url, node in graph.items()}
    new_trustrank_values = initial_values.copy()

    for iters in range(max_iterations):
        total_diff = 0.0
        for node_url, node in graph.items():
            pagerank_lost = 0
            if len(node.out) == 0:
                # Distribute TrustRank of dead-end nodes evenly
                pagerank_lost += damping_factor * trustrank_values[node_url]
            else:
                share = damping_factor * \
                    trustrank_values[node_url] / (len(node.out) + 1)
                for neighbor_url in node.out:
                    if neighbor_url in new_trustrank_values:
                        add_rank(new_trustrank_values, neighbor_url,
                                 share)
                    else:
                        # Loosing pagerank value here...add it back to trusted_nodes at the random_jump stage
                        pagerank_lost += share
                pagerank_lost += share * 1

            random_jump = (
                (1 - damping_factor) * trustrank_values[node_url] + pagerank_lost) / trusted_nodes_len

            for neighbor_url, multiplier in trusted_nodes:
                add_rank(new_trustrank_values, neighbor_url,
                         random_jump * multiplier)

        old_sum = sum(trustrank_values.values())
        new_sum = sum(new_trustrank_values.values())

        assert abs(old_sum - new_sum) <= 1

        for key in trustrank_values:
            total_diff += abs(new_trustrank_values[key] -
                              trustrank_values[key])

        trustrank_values = new_trustrank_values.copy()
        new_trustrank_values = initial_values.copy()

        if total_diff < tolerance:
            break
        else:
            print("Diff", total_diff)

        # print("Current values", trustrank_values)

    return trustrank_values


def insert_pagerank(db: Connection, pages: list[PageAsNode], scores: dict[str, float]):
    cursor = db.cursor()
    for p in pages:
        p.page_rank = scores[p.url]

    update_data = [(p.page_rank, p.id) for p in pages]

    update_statement = 'UPDATE "Page" SET page_rank = %s WHERE id = %s;'
    cursor.executemany(update_statement, update_data)
    db.commit()


def combine_domain_and_page_scores(domains: dict[str, float], pages: dict[str, float]) -> dict[str, float]:
    pages_combined = {}
    for url, page_score in pages.items():
        domain = url_to_domain(url)
        domain_score = domains[domain]

        pages_combined[url] = ((domain_score ** 2.0) * (page_score + 1)) + 1

    return pages_combined


def main():
    cursor = db.cursor(row_factory=kwargs_row(PageAsNode))
    pages = cursor.execute(
        "SELECT id, url,outbound_urls,depth  FROM \"Page\"").fetchall()
    json.dump([p.dict() for p in pages], open("/tmp/file.json", "w+"))
    # pages = json.load(open("/tmp/file.json", "r"))
    # pages = [PageAsNode(**p) for p in pages]
    print("Got pages", len(pages))

    nodes = Node.from_db(pages)
    domains = Node.convert_to_domains(nodes)

    topdomains = trustrank(domains)

    for domain in topdomains:
        topdomains[domain] = topdomains[domain] / \
            (domains[domain].individual_pages)

    topurls = trustrank(nodes, max_iterations=0)


    page_score = combine_domain_and_page_scores(topdomains, topurls)

    insert_pagerank(db, pages, page_score)


if __name__ == "__main__":
    main()
