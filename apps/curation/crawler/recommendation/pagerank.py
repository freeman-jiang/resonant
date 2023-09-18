import asyncio
from collections import defaultdict

from prisma import Prisma
from pydantic import BaseModel
from dotenv import load_dotenv
import random

load_dotenv()

prisma = Prisma()


class Node(BaseModel):
    out: list[str]
    url: str
    score: float

    @classmethod
    async def from_db(cls) -> dict[str, 'Node']:
        pages = await prisma.page.find_many()

        d = {p.url: Node(out=p.outbound_urls, url=p.url, score=((5 - p.depth) ** 3) / 64) for p in pages}
        for url, node in d.items():
            node.out = list(filter(lambda k: k in d, node.out))
        return d


def url_to_domain(url: str) -> str:
    answer = url.split('/')[2]

    if answer.startswith('www.'):
        answer = answer[4:]
    return answer


def print_top_domains(trustrank_values: dict):
    trust_domains = defaultdict(int)

    for url, score in trustrank_values.items():
        trust_domains[url_to_domain(url)] += score
    trustrank_sorted = [(url, score) for url, score in trust_domains.items()]
    trustrank_sorted.sort(key=lambda k: k[1])
    return trustrank_sorted


def trustrank(graph: dict[str, Node], damping_factor=0.85, max_iterations=100, tolerance=1e-2):
    trusted_nodes = [url for url, node in graph.items() if node.score >= 0.99]

    # Initialize TrustRank values
    trustrank_values = {url: node.score for url, node in graph.items()}
    initial_values = trustrank_values.copy()
    new_trustrank_values = trustrank_values.copy()

    for _ in range(max_iterations):
        total_diff = 0.0
        for node_url, node in graph.items():
            if len(node.out) == 0:
                # Distribute TrustRank of dead-end nodes evenly
                if len(graph[node_url].out) == 0:
                    dead_end_trustrank_share = (1 - damping_factor) * trustrank_values[node_url] / len(trusted_nodes)

                    for node_url in trusted_nodes:
                        new_trustrank_values[node_url] += dead_end_trustrank_share
            else:
                share = damping_factor * trustrank_values[node_url] / len(node.out)
                for neighbor_url in node.out:
                    # Only propagate TrustRank to trusted nodes
                    new_trustrank_values[neighbor_url] += damping_factor * share

        for key in trustrank_values:
            total_diff += abs(new_trustrank_values[key] - trustrank_values[key])
        trustrank_values = new_trustrank_values.copy()
        new_trustrank_values = initial_values.copy()

        if total_diff < tolerance:
            break
        else:
            print(total_diff)
            print(print_top_domains(trustrank_values))

        # print("Current values", trustrank_values)

    return print_top_domains(trustrank_values)


async def main():
    await prisma.connect()
    nodes = await Node.from_db()
    trustrank(nodes)


def test_a():
    asyncio.run(main())
