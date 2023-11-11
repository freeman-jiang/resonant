// Heavily inspired by the Quartz graph view
import { PageNode } from "@/api";
import * as d3 from "d3";

type NodeData = PageNode & d3.SimulationNodeDatum;

type LinkData = {
  source: string;
  target: string;
};

const localGraph = {
  drag: true,
  zoom: true,
  depth: 1,
  scale: 1.1,
  repelForce: 0.5,
  centerForce: 0.3,
  linkDistance: 30,
  fontSize: 0.6,
  opacityScale: 1,
  showTags: true,
  removeTags: [],
};

export const renderGraph = (
  id: string,
  node: PageNode,
  neighbors: PageNode[],
) => {
  const graph = document.getElementById(id);
  const links: LinkData[] = [];

  for (const neighbor of neighbors) {
    links.push({ source: node.url, target: neighbor.url });
  }

  const nodes: NodeData[] = [node, ...neighbors].map((node) => ({
    ...node,
  }));

  const graphData: { nodes: NodeData[]; links: LinkData[] } = { nodes, links };

  const simulation: d3.Simulation<NodeData, LinkData> = d3
    .forceSimulation(graphData.nodes)
    .force("charge", d3.forceManyBody().strength(-100 * localGraph.repelForce))
    .force(
      "link",
      d3
        .forceLink(graphData.links)
        .id((d: NodeData) => d.url) // custom id accessor
        .distance(localGraph.linkDistance),
    )
    .force("center", d3.forceCenter().strength(localGraph.centerForce));

  const height = Math.max(graph.offsetHeight, 250);
  const width = graph.offsetWidth;

  const boundingBox = d3
    .select<HTMLElement, NodeData>(`#${id}`)
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", [
      -width / 2 / localGraph.scale,
      -height / 2 / localGraph.scale,
      width / localGraph.scale,
      height / localGraph.scale,
    ])
    .attr("class", "bg-slate-100");

  // draw links between nodes
  const svgLinks = boundingBox
    .append("g")
    .selectAll("line")
    .data(graphData.links)
    .join("line")
    .attr("class", "stroke-slate-500")
    .attr("stroke-width", 1);

  // svg groups
  const graphNode = boundingBox
    .append("g")
    .selectAll("g")
    .data(graphData.nodes)
    .enter()
    .append("g");

  const svgNodes = graphNode
    .append("circle")
    .attr("class", "fill-emerald-500 h-4 w-4")
    .attr("id", (d) => d.id)
    .attr("r", 4)
    .style("cursor", "pointer");

  // progress the simulation
  simulation.on("tick", () => {
    // Draw the links
    svgLinks
      .attr("x1", (d: any) => d.source.x)
      .attr("y1", (d: any) => d.source.y)
      .attr("x2", (d: any) => d.target.x)
      .attr("y2", (d: any) => d.target.y);

    svgNodes.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
  });
};
