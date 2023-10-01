import json
import plotly.express as px

from matplotlib import pyplot as plt
from sklearn.cluster import KMeans

from crawler.recommendation.pagerank import PageAsNode, Node
import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD


def to_bitmaps(pages: list[Node]):
    total_pages = len(pages)
    url_to_index = {p.url: i for i, p in enumerate(pages)}

    linked_to = {}

    for p in pages:
        for out in p.out:
            if out not in linked_to:
                linked_to[out] = np.zeros(total_pages)
            linked_to[out][url_to_index[p.url]] += 1


    return linked_to


def get_domain_graph(pages: list[Node]):
    domain_bitmaps = to_bitmaps(pages)

    # Apply PCA dimensionality reduction
    # Apply PCA dimensionality reduction to each vector in domain_bitmaps
    reduced_bitmaps = {}

    bitmaps = list(domain_bitmaps.values())

    print("PCA transforming...")
    model = TruncatedSVD()
    model.fit(bitmaps[0:30000])
    print("Done training!")

    for url, bitmap in domain_bitmaps.items():
        reduced = model.transform([bitmap])
        reduced_bitmaps[url] = reduced[0] # Assuming you want a 1D array as the result

    print("Done!")
    return reduced_bitmaps


def plot_clusters_with_plotly(urls, reduced_bitmaps, n_clusters=10):
    # Cluster the data using K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    clusters = kmeans.fit_predict(reduced_bitmaps)
    x = reduced_bitmaps
    reduced_bitmaps = np.sign(x) * np.abs(x) ** (1 / 57)
    # Create a DataFrame for Plotly
    import pandas as pd
    data = pd.DataFrame(
        {'URL': urls, 'Component 1': reduced_bitmaps[:, 0], 'Component 2': reduced_bitmaps[:, 1], 'Cluster': clusters})

    # Create a scatter plot using Plotly
    fig = px.scatter(data, x='Component 1', y='Component 2', color='Cluster', text='URL', title='Clustered Vectors')
    fig.update_traces(textposition='top center')
    fig.update_layout(showlegend=False)
    fig.write_html('clustered_vectors.html')


if __name__ == "__main__":
    import pickle
    pages = json.load(open("/tmp/file.json", "r"))
    pages = [PageAsNode(**p) for p in pages]
    nodes = Node.from_db(pages)
    domains = Node.convert_to_domains(nodes)

    reduced_bitmaps = get_domain_graph(list(domains.values()))
    #
    pickle.dump(reduced_bitmaps, open("reduced_bitmaps.pkl", "wb+"))
    reduced_bitmaps = pickle.load(open("reduced_bitmaps.pkl", "rb+"))

    plot_clusters_with_plotly(list(reduced_bitmaps.keys()), np.array(list(reduced_bitmaps.values())))
