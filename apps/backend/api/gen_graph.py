import json

from api.main import D3Link, NodePage, PageNodesResponse
from crawler.prismac import PostgresClient, pg_client
from pydantic import BaseModel
from pydantic.json import pydantic_encoder

pg_client.connect()
print('Sending query')
root_url = "https://hypertext.joodaloop.com/"
pages = pg_client.get_network(root_url, 11)
print('Finished query')
adjacency_list = {p.url: p for p in pages}


links: list[D3Link] = []

for neighbor in adjacency_list.values():
    for outbound_link in neighbor.outbound_urls:
        if outbound_link in adjacency_list:
            link = D3Link(source=neighbor.url, target=outbound_link)
            links.append(link)

nodes = list(adjacency_list.values())

precomputed_global_graph = PageNodesResponse(
    nodes=nodes, links=links, root_url=root_url)

# write to file 'graph.json'
# This will be run in the context of apps/backend and thus write to apps/web/public/graph.json
with open('../web/public/graph.json', 'w') as f:
    f.write(precomputed_global_graph.json())
