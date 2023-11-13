import json

import networkx as nx
import plotly.graph_objects as go
from networkx.algorithms.community import greedy_modularity_communities
from psycopg.rows import kwargs_row

from crawler.dbaccess import db
from crawler.recommendation.nodes import PageAsNode, Node


def plot_communities(graph):
    print("Getting communities")
    graph = graph.subgraph(node for node in graph.nodes if graph.degree[node] != 0)

    # Delete nodes with no edges
    # Find communities using Louvain method
    communities = list(greedy_modularity_communities(graph, weight='weight', resolution=1.9))
    print("Done communities")


    file = open("/tmp/log.txt" , 'w+')
    for c in communities:
        print(c, file = file)

    # Assign community labels to nodes
    node_community_mapping = {node: i for i, comm in enumerate(communities) for node in comm}

    pg_comm = node_community_mapping['crystalzhang.substack.com']
    pg_comm_graph = graph.subgraph(node for node in graph.nodes if node_community_mapping[node] == pg_comm)
    graph = pg_comm_graph

    # for edge in graph.edges:
    #     source, target = edge
    #     if node_community_mapping[source] == node_community_mapping[target]:
    #         # Nodes are in the same community, double the weight
    #         print("Doubling weight", source, target)
    #         graph[source][target]['weight'] += 2
    #     else:
    #         graph[source][target]['weight'] += -2


    # Create a Plotly scatter plot for the nodes with community color-coding
    node_trace_x = []
    node_trace_y = []
    node_trace_text = []


    pos = nx.spring_layout(graph, iterations = 100)

    for node in graph.nodes:
        x, y = pos[node]
        node_trace_x.append(x)
        node_trace_y.append(y)
        node_trace_text.append(f'{node}')

    node_trace = go.Scatter(
        x=node_trace_x,
        y=node_trace_y,
        text=node_trace_text,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=10,
            colorbar=dict(
                thickness=15,
                title='Community',
                xanchor='left',
                titleside='right'
            )
        )
    )

    node_trace['marker']['color'] = [node_community_mapping[node] for node in graph.nodes]
    node_trace['marker']['colorbar']['tickvals'] = list(range(len(communities)))
    node_trace['marker']['colorbar']['ticktext'] = [str(i) for i in range(len(communities))]

    # Plot edges
    edge_x = []
    edge_y = []

    for edge in graph.edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Create a Plotly graph layout
    layout = go.Layout(
        showlegend=False,
        hovermode='closest',
    )

    # Create a Plotly figure
    fig = go.Figure(data=[node_trace, edge_trace], layout=layout)

    # Save the figure to an HTML file
    fig.write_html("community_plot1.html")
    # Create a Plotly graph layout

# Assuming you have a graph variable named 'your_graph'
# your_graph = convert_to_networkx_graph(nodes_dict)

# Use the function to plot communities and save to HTML

def convert_to_networkx_graph(nodes: dict[str, 'Node']) -> nx.Graph:
    G = nx.Graph()

    for url, node in nodes.items():
        G.add_node(node.url, score=node.score, best_depth=node.best_depth, individual_pages=node.individual_pages)

        curweight = 1 / (len(node.out) + 1)
        for out_url in node.out:
            if G.has_edge(node.url, out_url):
                # Edge already exists, increment weight by 1
                G[node.url][out_url]['weight'] += curweight
            else:
                # Edge doesn't exist, add a new edge with weight 1
                G.add_edge(node.url, out_url, weight=curweight)


    return G

def main():
    cursor = db.cursor(row_factory=kwargs_row(PageAsNode))
    pages = cursor.execute(
        "SELECT id, url,outbound_urls,depth  FROM \"Page\" WHERE COALESCE(page_rank, 0) >= 2.3 LIMIT 500000").fetchall()
    json.dump([p.dict() for p in pages], open("/tmp/file.json", "w+"))
    pages = json.load(open("/tmp/file.json", "r"))
    pages = [PageAsNode(**x) for x in pages]

    nodes = Node.from_db(pages)
    domains = Node.convert_to_domains(nodes)

    print("Domain length", len(domains))
    graph = convert_to_networkx_graph(domains)
    plot = plot_communities(graph)

    return


main()
