from pydantic import BaseModel


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
    def from_db(cls, pages: list[PageAsNode]) -> dict[str, 'Node']:
        for p in pages:
            domain = url_to_domain(p.url)
            p.outbound_urls = [x for x in p.outbound_urls if x != p.url]
            p.outbound_urls = [
                x for x in p.outbound_urls if url_to_domain(x) != domain]

        d = {p.url: Node(out=p.outbound_urls, url=p.url, score=(
            (5 - p.depth) ** 4) / 100, best_depth=p.depth) for p in pages}

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
