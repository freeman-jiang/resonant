
import asyncio

from psycopg import Connection
from psycopg.rows import kwargs_row

from crawler.recommendation.embedding import db
from prisma import models

from prisma import Prisma
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

prisma = Prisma()


class PageAsNode(BaseModel):
    id: int
    url: str
    outbound_urls: list[str]
    depth: int

    page_rank: int = 0


class Node(BaseModel):
    out: list[str]
    url: str
    score: float
    best_depth: int

    individual_pages: int = 1

    @classmethod
    async def from_db(cls, pages: list[PageAsNode]) -> dict[str, 'Node']:
        for p in pages:
            domain = url_to_domain(p.url)
            p.outbound_urls = [x for x in p.outbound_urls if x != p.url]
            p.outbound_urls = [x for x in p.outbound_urls if url_to_domain(x) != domain]

        d = {p.url: Node(out=p.outbound_urls, url=p.url, score=(
            (5 - p.depth) ** 2.5), best_depth=p.depth) for p in pages}

        return d

    @classmethod
    def convert_to_domains(cls, nodes: dict[str, 'Node']):
        answer = {}
        for url, node in nodes.items():

            domain = url_to_domain(url)

            if domain not in answer:
                answer[domain] = Node(out=[], url=domain,
                                      score=0, best_depth=node.best_depth)

            out = [url_to_domain(x) for x in node.out]
            out = [x for x in out if x != domain]

            answer[domain].out += out
            answer[domain].score += node.score
            answer[domain].individual_pages += 1
            answer[domain].best_depth = min(
                answer[domain].best_depth, node.best_depth)
        return answer


def url_to_domain(url: str) -> str:
    if url.startswith("https://") or url.startswith("http://"):
        index = 2
    else:
        index = 0

    answer = url.split('/')[index]

    if answer.startswith('www.'):
        answer = answer[4:]

    return answer


def top_domains(trustrank_values: dict) -> dict[str, float]:
    trustrank_values_sorted = sorted(
        [(k, v) for k, v in trustrank_values.items()], key=lambda k: k[1])
    return trustrank_values_sorted


from collections import defaultdict
NORMAL_ADDS = defaultdict(int)
def add_rank(d, url, value, msg=""):
    global NORMAL_ADDS
    if msg.startswith('normal'):
        NORMAL_ADDS[url] += value

    d[url] += value


def trustrank(graph: dict[str, Node], damping_factor=0.82, max_iterations=100, tolerance=1.0):
    trusted_nodes = [(url, node.individual_pages)
                     for url, node in graph.items() if node.best_depth <= 1]
    trusted_nodes_len = sum(
        x.individual_pages for x in graph.values() if x.best_depth <= 1)

    # Initialize TrustRank values
    trustrank_values = {url: node.score for url, node in graph.items()}
    initial_values = {url: 0 for url, node in graph.items()}
    new_trustrank_values = initial_values.copy()

    for iters in range(max_iterations):
        NORMAL_ADDS.clear()
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
                                 share, f'normal-{node_url}')
                    else:
                        # Loosing pagerank value here...add it back to trusted_nodes at the random_jump stage
                        # print("Out-link to domain that we don't know: ", neighbor_url)
                        pagerank_lost += share
                pagerank_lost += share * 1

            random_jump = (
                (1 - damping_factor) * trustrank_values[node_url] + pagerank_lost) / trusted_nodes_len

            for neighbor_url, multiplier in trusted_nodes:
                add_rank(new_trustrank_values, neighbor_url,
                         random_jump * multiplier, 'random' if iters >= 6 else 'fda')

        old_sum = sum(trustrank_values.values())
        new_sum = sum(new_trustrank_values.values())

        assert abs(old_sum - new_sum) <= 1e-1

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

    min_trusted = 100000
    for url, _ in trusted_nodes:
        min_trusted = min(min_trusted, trustrank_values[url])
    print("Min trusted node is", min_trusted)
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

        pages_combined[url] = ((domain_score ** 0.4) * (page_score + 1))

    return pages_combined


async def main():
    await prisma.connect()
    cursor = db.cursor(row_factory=kwargs_row(PageAsNode))
    pages = cursor.execute(
        "SELECT id, url,outbound_urls,depth  FROM \"Page\" WHERE created_at <= timestamp '2023-09-26' LIMIT 120000").fetchall()
    # json.dump([p.dict() for p in pages], open("/tmp/file.json", "w+"))
    #
    # pages = json.load(open("/tmp/file.json", "r"))
    # pages = [PageAsNode(**p) for p in pages]
    print(pages, file=open("pages.txt", "w+"))
    print("Got pages", len(pages))

    nodes = await Node.from_db(pages)
    domains = Node.convert_to_domains(nodes)

    topdomains = trustrank(domains)

    for domain in topdomains:
        topdomains[domain] = topdomains[domain] / (domains[domain].individual_pages)

    topurls = trustrank(nodes)
    page_score = combine_domain_and_page_scores(topdomains, topurls)

    print(topdomains, file = open("topdomains.txt", "w+"))
    print(topurls, file = open("topurls.txt", "w+"))
    insert_pagerank(db, pages, page_score)




if __name__ == "__main__":
    asyncio.run(main())
