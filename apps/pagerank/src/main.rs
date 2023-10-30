mod tests;

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;

#[derive(Deserialize, Serialize)]
struct PageAsNode {
    id: i32,
    url: String,
    outbound_urls: Vec<String>,
    depth: i32,

    #[serde(default)]
    page_rank: i32,
}

#[derive(Deserialize, Serialize, Default, Clone)]
struct Node {
    id: i32,
    out: Vec<String>,
    url: String,
    score: f64,
    best_depth: i32,

    individual_pages: i32,
}


impl Node {
    pub fn preprocess_url(url: String) -> String {
        let mut result = url;

        // Remove protocol
        if result.starts_with("http://") {
            result = result["http://".len()..].to_string();
        } else if result.starts_with("https://") {
            result = result["https://".len()..].to_string();
        }

        // Remove www.
        if result.starts_with("www.") {
            result = result["www.".len()..].to_string();
        }

        // Remove query parameters
        if let Some(i) = result.find('?') {
            result = result[..i].to_string();
        }

        result
    }

    fn preprocess_urls_for_pages(mut pages: Vec<PageAsNode>) -> Vec<PageAsNode> {
        for p in &mut pages {
            p.url = Node::preprocess_url(std::mem::take(&mut p.url));

            for out in &mut p.outbound_urls {
                *out = Node::preprocess_url(std::mem::take(out));
            }
        }

        pages
    }
    fn from_db(pages: Vec<PageAsNode>) -> HashMap<String, Node> {
        let pages = Node::preprocess_urls_for_pages(pages);

        let mut nodes = HashMap::new();

        for page in pages {
            let domain = url_to_domain(&page.url);
            let outbound = page
                .outbound_urls
                .iter()
                .filter(|url| **url != page.url)
                .filter(|url| url_to_domain(url) != domain)
                .cloned()
                .collect();

            let node = Node {
                id: page.id,
                out: outbound,
                url: page.url.clone(),
                score: 1.0,
                best_depth: page.depth,
                individual_pages: 1,
            };

            nodes.insert(page.url, node);
        }

        nodes
    }

    fn convert_to_domains(nodes: &HashMap<String, Node>) -> HashMap<String, Node> {
        let mut domains = HashMap::new();

        for (url, node) in nodes {
            let domain = url_to_domain(&url);

            let entry = domains.entry(domain).or_insert_with_key(|domain| Node {
                out: vec![],
                url: domain.to_string(),
                score: 0.0,
                best_depth: node.best_depth,
                ..Default::default()
            });

            let out: Vec<_> = node
                .out
                .iter()
                .map(|url| url_to_domain(url))
                .filter(|domain| **domain != entry.url)
                .collect();

            entry.out.extend(out);
            entry.score += node.score;
            entry.individual_pages += 1;
            entry.best_depth = entry.best_depth.min(node.best_depth);
        }

        domains
    }
}

fn url_to_domain(url: &str) -> String {
    let domain = if url.starts_with("https://") {
        &url[8..]
    } else if url.starts_with("http://") {
        &url[7..]
    } else {
        url
    }
    .split('/')
    .next()
    .unwrap();

    let mut domain = domain.to_string();
    if domain.starts_with("www.") {
        domain.drain(..4);
    }

    domain
}

#[test]
fn test_url_to_domain() {
    assert_eq!(
        "yalereview.org",
        url_to_domain("https://yalereview.org/article/stalking-1")
    );
    assert_eq!(
        "yalereview.org",
        url_to_domain("https://www.yalereview.org/article/stalking-1")
    );
    assert_eq!(
        "poradnikprzedsiebiorcy.pl",
        url_to_domain(
            "https://poradnikprzedsiebiorcy.pl/-co-to-jest-podatek-vat-zasady-jego-dzialania"
        )
    )
}


struct OptimizedGraph {
    nodes: Vec<Node>,
    adj: Vec<Vec<usize>>,
    urls: Vec<String>,
    reverse_url_map: HashMap<String, usize>,
}

struct GraphIterator<'a> {
    graph: &'a OptimizedGraph,
    index: usize,
}

impl<'a> Iterator for GraphIterator<'a> {
    type Item = (usize, &'a Node);

    fn next(&mut self) -> Option<Self::Item> {
        if self.index >= self.graph.nodes.len() {
            return None;
        }

        let i = self.index;
        self.index += 1;

        let node = &self.graph.nodes[i];

        Some((i, node))
    }
}

impl OptimizedGraph {
    fn new(nodes: Vec<Node>, adj: Vec<Vec<usize>>, urls: Vec<String>) -> Self {
        let reverse_url_map = urls
            .iter()
            .enumerate()
            .map(|(index, url)| (url.clone(), index))
            .collect();

        Self {
            nodes,
            adj,
            urls,
            reverse_url_map,
        }
    }
    fn iter(&self) -> GraphIterator {
        GraphIterator {
            graph: self,
            index: 0,
        }
    }

    fn convert_graph_to_ids(graph: &HashMap<String, Node>) -> Self {
        /// Converts the graph to use integer IDs (as indexes into a vector) instead of URLs for performance

        // Map URLs -> monotonically increasing IDs
        let mut current_id: usize = 0;
        let mut url_map = HashMap::new();

        for (url, node) in graph {
            url_map.insert(url.as_str(), current_id);
            current_id += 1;
        }

        let mut nodes = Vec::new();
        let mut adj: Vec<Vec<usize>> = Vec::new();
        let mut urls: Vec<String> = vec![Default::default(); current_id];

        nodes.resize(current_id, Default::default());
        adj.resize(current_id, Default::default());

        for (url, index) in &url_map {
            let url = *url;

            urls[*index] = url.to_string();
            nodes[*index] = graph[url].clone();

            // Generate the adj list from the list of node.out
            let adj_list = &mut adj[*index];
            for out in &nodes[*index].out {
                let out_index = url_map.get(out.as_str()).unwrap_or(&usize::MAX);
                adj_list.push(*out_index);
            }
        }

        OptimizedGraph::new(nodes, adj, urls)
    }
}

fn get_trusted_nodes_list(graph: &OptimizedGraph) -> (Vec<(usize, f64)>, f64) {
    let trusted_nodes = graph
        .iter()
        .filter(|(_, node)| node.best_depth <= 1)
        .map(|(index, node)| {
            if node.best_depth == 0 {
                (index, node.individual_pages as f64 * 5.0)
            } else {
                (index, node.individual_pages as f64)
            }
        })
        .collect::<Vec<_>>();
    let sum_trusted_pages = trusted_nodes.iter().map(|(_, count)| count).sum::<f64>();

    (trusted_nodes, sum_trusted_pages)
}

fn trustrank(
    graph: &OptimizedGraph,
    max_iterations: i32,
    tolerance: f64,
    quiet: bool,
) -> HashMap<String, f64> {
    let damping_factor = 0.90;
    if !quiet {
        println!("Running trustrank on {} nodes!", graph.nodes.len());
    }

    let (trusted_nodes, sum_trusted_pages) = get_trusted_nodes_list(&graph);

    let mut trustrank_values: Vec<f64> = graph.iter().map(|(_, node)| node.score).collect();

    let zero_trustrank_template: Vec<f64> = graph.iter().map(|_| (0.0)).collect();

    let mut new_trustrank_values = zero_trustrank_template.clone();

    for _ in 0..max_iterations {
        let mut random_jump_accum = 0.0;

        for (idx, node) in graph.iter() {
            let adj = &graph.adj[idx];
            let mut rank_lost = 0.0;

            if adj.is_empty() {
                rank_lost += damping_factor * trustrank_values[idx];
            } else {
                let share = damping_factor * trustrank_values[idx] / adj.len() as f64;

                for neighbor in adj {
                    let neighbor = *neighbor;

                    if neighbor != usize::MAX {
                        new_trustrank_values[neighbor] += share;
                    } else {
                        rank_lost += share;
                    }
                }
            }

            let jump = (1.0 - damping_factor) * trustrank_values[idx] + rank_lost;
            let jump = jump / sum_trusted_pages;

            random_jump_accum += jump;
        }
        for (trusted_url, multiplier) in &trusted_nodes {
            new_trustrank_values[*trusted_url] += random_jump_accum * multiplier;
        }

        let diff: f64 = new_trustrank_values
            .iter()
            .zip(trustrank_values.iter())
            .map(|(a, b)| (a - b).abs())
            .sum();

        let trustrank_sum: f64 = trustrank_values.iter().sum();
        let new_trustrank_sum: f64 = new_trustrank_values.iter().sum();

        assert!(
            (trustrank_sum - new_trustrank_sum).abs() < 1.0,
            "{} {}",
            trustrank_sum,
            new_trustrank_sum
        );
        trustrank_values = new_trustrank_values.clone();

        if diff < tolerance {
            break;
        } else if !quiet {
            println!("Diff is {}", diff);
        }
        new_trustrank_values = zero_trustrank_template.clone();
    }

    new_trustrank_values
        .iter()
        .enumerate()
        .map(|(idx, score)| (graph.urls[idx].clone(), *score))
        .collect()
}

fn combine_scores(
    domain_scores: HashMap<String, f64>,
    page_scores: HashMap<String, f64>,
) -> Vec<(String, f64)> {
    let mut combined = Vec::new();

    for (url, page_score) in page_scores {
        let domain = url_to_domain(&url);
        let domain_score = domain_scores[&domain];

        let score = domain_score.powf(0.25) * (page_score + 1.0);

        combined.push((url, score));
    }

    combined
}

fn top_domains(mut scores: Vec<(String, i32, f64)>, limit: usize) {
    scores.sort_by(|a, b| a.2.partial_cmp(&b.2).unwrap().reverse());

    for i in 0..limit {
        println!("{:?}", &scores[i]);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let quiet = args.contains(&"quiet".to_string());
    // Load data from JSON file
    let data: Vec<PageAsNode> =
        serde_json::from_str(&std::fs::read_to_string("/tmp/file.json").unwrap()).unwrap();

    let nodes = Node::from_db(data);
    let domains = Node::convert_to_domains(&nodes);

    let node_graph = OptimizedGraph::convert_graph_to_ids(&nodes);
    let domain_graph =  OptimizedGraph::convert_graph_to_ids(&domains);

    let mut domain_scores = trustrank(&domain_graph, 100, 1.0, quiet);
    for (domain, score) in &mut domain_scores {
        *score /= domains[domain].individual_pages as f64;
    }

    let page_scores = trustrank(&node_graph, 100, 1.0, quiet);

    let combined_scores = combine_scores(domain_scores, page_scores);

    let scores_with_ids: Vec<_> = combined_scores.into_iter().map(|(cleaned_url, score)| {
        let idx = node_graph.reverse_url_map[&cleaned_url];
        let id = node_graph.nodes[idx].id;
        (cleaned_url, id, score)
    }).collect();

    // Insert scores into database
    let limit = if quiet {
        scores_with_ids.len()
    } else {
        1000
    };
    top_domains(scores_with_ids, limit);
}
