import asyncio
from collections import defaultdict

from prisma import Prisma
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

prisma = Prisma()


class Node(BaseModel):
    out: list[str]
    url: str
    score: float
    best_depth: int

    individual_pages: int = 1

    @classmethod
    async def from_db(cls) -> dict[str, 'Node']:
        pages = await prisma.page.find_many()


        d = {p.url: Node(out=p.outbound_urls, url=p.url, score=(
            (3 - p.depth) ** 4) / 27, best_depth = p.depth) for p in pages}
        # for url, node in d.items():
        #     if url == 'https://danluu.com/filesystem-errors/':
        #         wtf = 5
        #     node.out = list(filter(lambda k: k in d, node.out))
        return d

    @classmethod
    def convert_to_domains(cls, nodes: dict[str, 'Node']):
        answer = {}
        for url, node in nodes.items():

            domain = url_to_domain(url)

            if domain not in answer:
                answer[domain] = Node(out=[], url=domain, score=0, best_depth = node.best_depth)

            out = [url_to_domain(x) for x in node.out]
            # out = [x for x in out if x != domain]

            answer[domain].out += out
            answer[domain].score += node.score
            answer[domain].individual_pages += 1
            answer[domain].best_depth = min(answer[domain].best_depth, node.best_depth)
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


def top_domains(graph: dict[str, Node], trustrank_values: dict):
    trust_domains = defaultdict(int)
    trust_domains_len = defaultdict(int)

    for url, score in trustrank_values.items():
        trust_domains[url_to_domain(url)] += score
        trust_domains_len[url_to_domain(url)] += graph[url].individual_pages

    trustrank_sorted = [(url, score / (trust_domains_len[url] + 3), trust_domains_len[url]) for url, score in trust_domains.items()]
    trustrank_sorted.sort(key=lambda k: k[1])

    trustrank_values_sorted = sorted([(k, v) for k, v in trustrank_values.items()], key=lambda k: k[1])
    return trustrank_sorted, trustrank_values_sorted


def trustrank(graph: dict[str, Node], damping_factor=0.70, max_iterations=100, tolerance=1e-3):
    trusted_nodes = [url for url, node in graph.items() if node.best_depth <= 1]

    # Initialize TrustRank values
    trustrank_values = {url: node.score for url, node in graph.items()}
    initial_values = {url: 0 for url, node in graph.items()}
    new_trustrank_values = initial_values.copy()

    for _ in range(max_iterations):
        total_diff = 0.0
        for node_url, node in graph.items():
            pagerank_lost = 0
            if len(node.out) == 0:
                # Distribute TrustRank of dead-end nodes evenly
                if len(graph[node_url].out) == 0:
                    dead_end_trustrank_share = damping_factor * trustrank_values[node_url] / len(trusted_nodes)

                    for neighbor_url in trusted_nodes:
                        new_trustrank_values[neighbor_url] += dead_end_trustrank_share
            else:
                share = damping_factor * \
                    trustrank_values[node_url] / len(node.out)
                for neighbor_url in node.out:
                    if neighbor_url in new_trustrank_values:
                        new_trustrank_values[neighbor_url] += share
                    else:
                        # Loosing pagerank value here...add it back to trusted_nodes at the random_jump stage
                        # print("Out-link to domain that we don't know: ", neighbor_url)
                        pagerank_lost += share

            random_jump = ((1 - damping_factor) * trustrank_values[node_url] + pagerank_lost) / len(trusted_nodes)

            for neighbor_url in trusted_nodes:
                new_trustrank_values[neighbor_url] += random_jump


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
            print(total_diff)

        # print("Current values", trustrank_values)
    return top_domains(graph, trustrank_values)


async def main():
    await prisma.connect()
    nodes = await Node.from_db()
    nodes = Node.convert_to_domains(nodes)

    topdomains, topurls = trustrank(nodes)
    # scored_by_num_articles = sorted([(x[2] / x[1], x[0]) for x in topdomains])

    # print(topdomains)

    print(*topurls, sep = '\n')


if __name__ == "__main__":
    asyncio.run(main())
