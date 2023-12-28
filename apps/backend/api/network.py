import json

from api.main import PageNode
from crawler.prismac import PostgresClient, pg_client
from pydantic import BaseModel
from pydantic.json import pydantic_encoder

pg_client.connect()
print('Getting network')
pages = pg_client.get_network("https://hypertext.joodaloop.com/", 10)
print('Got network')
root = pages[0]
adjacency_list = {p.url: PageNode.from_page(p) for p in pages}


class D3Link(BaseModel):
    source: str
    target: str


links: list[D3Link] = []

for neighbor in adjacency_list.values():
    for outbound_link in neighbor.outboundUrls:
        if outbound_link in adjacency_list:
            link = D3Link(source=neighbor.url, target=outbound_link)
            links.append(link)

nodes = list(adjacency_list.values())

json_result = json.dumps(
    {"nodes": nodes, "links": links}, default=pydantic_encoder)

# write to file 'graph.json'
with open('graph.json', 'w') as f:
    f.write(json_result)
