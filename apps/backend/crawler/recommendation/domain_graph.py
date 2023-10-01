import json
import plotly.express as px

from matplotlib import pyplot as plt
from sklearn.cluster import KMeans

from crawler.recommendation.pagerank import PageAsNode, Node
import numpy as np
from sklearn.decomposition import PCA, TruncatedSVD


def to_bitmaps(pages: list[Node]):
    total_pages = set()
    for p in pages:
        total_pages.update(p.out)
        total_pages.add(p.url)

    total_pages_len = len(total_pages)
    url_to_index = {p: i for i, p in enumerate(total_pages)}

    # linked_to = {}
    links_out = {}

    for p in pages:
        if p.url not in links_out:
            links_out[p.url] = np.zeros(total_pages_len)

        for out in p.out:
            # if out not in links_out:
            #     links_out[out] = np.zeros(total_pages_len * 2 + 1)
            # links_out[out][url_to_index[p.url] + total_pages_len] += 1

            links_out[p.url][url_to_index[out]] += 1

    return links_out


def get_domain_graph(pages: list[Node]):
    domain_bitmaps = to_bitmaps(pages)

    # Apply PCA dimensionality reduction
    # Apply PCA dimensionality reduction to each vector in domain_bitmaps

    urls = list(domain_bitmaps.keys())
    bitmaps = list(domain_bitmaps.values())

    print("PCA transforming...")
    model = TruncatedSVD(n_components=2)
    reduced_bitmaps_list = model.fit_transform(bitmaps)

    reduced_bitmaps = {k: v for k, v in zip(urls, reduced_bitmaps_list)}

    return reduced_bitmaps


def plot_clusters_with_plotly(urls, reduced_bitmaps, n_clusters=150):
    # Cluster the data using K-Means
    x = reduced_bitmaps
    reduced_bitmaps = np.sign(x) * np.abs(x) ** (1 / 31)
    kmeans = KMeans(n_clusters=n_clusters, random_state=0)
    clusters = kmeans.fit_predict(reduced_bitmaps)
    # Create a DataFrame for Plotly
    import pandas as pd
    data = pd.DataFrame(
        {'URL': urls, 'Component 1': reduced_bitmaps[:, 0], 'Component 2': reduced_bitmaps[:, 1], 'Cluster': clusters})

    df1 = data.groupby('Cluster')['URL'].apply(list)
    df1.to_csv("clusters.csv")

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
