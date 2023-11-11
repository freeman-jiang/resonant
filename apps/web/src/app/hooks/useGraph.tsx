// Heavily inspired by the Quartz graph view
import { PageNode } from "@/api";
import * as d3 from "d3";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

type NodeData = PageNode & d3.SimulationNodeDatum;

type LinkData = {
  source: string;
  target: string;
};

type LinkDatum = {
  index: 0;
  source: NodeData;
  target: NodeData;
};

const localGraph = {
  drag: true,
  zoom: true,
  depth: 1,
  scale: 1.1,
  repelForce: 1,
  centerForce: 0.3,
  linkDistance: 100,
  fontSize: 0.6,
  opacityScale: 2.5,
  showTags: true,
  removeTags: [],
};

const defaultLinkColor = "#d8dee9"; // grey
const activeLinkColor = "#94a3b8";
const defaultNodeColor = "#80eaa5"; // green
const activeNodeColor = "#38d5f5"; // bright blue

const initialOpacity = (localGraph.opacityScale - 1) / 3.75;

const getLabelId = (id: number) => `labelfor-${id}`;

let didInit = false;

// Expects there to be an empty div with the given id
export const useGraph = (
  id: string,
  pageNode: PageNode,
  neighbors: PageNode[],
) => {
  const router = useRouter();

  const renderGraph = () => {
    const graph = document.getElementById(id);
    const links: LinkData[] = [];

    for (const neighbor of neighbors) {
      links.push({ source: pageNode.url, target: neighbor.url });
    }

    const nodes: NodeData[] = [pageNode, ...neighbors].map((node) => {
      return { ...node, title: node.title };
    });

    const graphData: { nodes: NodeData[]; links: LinkData[] } = {
      nodes,
      links,
    };

    const simulation: d3.Simulation<NodeData, LinkData> = d3
      .forceSimulation(graphData.nodes)
      .force(
        "charge",
        d3.forceManyBody().strength(-100 * localGraph.repelForce),
      )
      .force(
        "link",
        d3
          .forceLink(graphData.links)
          .id((d: NodeData) => d.url) // custom id accessor
          .distance(localGraph.linkDistance),
      )
      .force("center", d3.forceCenter().strength(localGraph.centerForce));

    const height = Math.max(graph.offsetHeight, 400);
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
      ]);
    // .attr("class", "bg-black");

    // draw links between nodes
    const svgLinks = boundingBox
      .append("g")
      .selectAll("line")
      .data(graphData.links)
      .join("line")
      .attr("class", "graph-link")
      .attr("stroke", defaultLinkColor)
      .attr("stroke-width", 1);

    // Container for all the nodes
    const graphNode = boundingBox
      .append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .enter();

    const drag = (simulation: d3.Simulation<NodeData, LinkData>) => {
      function dragstarted(event: any, d: NodeData) {
        if (!event.active) simulation.alphaTarget(1).restart();
        d.fx = d.x;
        d.fy = d.y;
      }

      function dragged(event: any, d: NodeData) {
        d.fx = event.x;
        d.fy = event.y;
      }

      function dragended(event: any, d: NodeData) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      }

      return d3
        .drag<Element, NodeData>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    };

    // calculate color
    const nodeClass = (d: NodeData): string => {
      const isCurrent = d.url === pageNode.url;
      if (isCurrent) {
        return "graph-node-current";
      }
      return "graph-node";
    };

    // calculate node fill color
    const nodeFill = (d: NodeData): string => {
      const isCurrent = d.url === pageNode.url;
      if (isCurrent) {
        return activeNodeColor;
      }
      return defaultNodeColor;
    };

    const nodeRadius = (d: NodeData): number => {
      const isCurrent = d.url === pageNode.url;
      if (isCurrent) {
        return 4;
      }
      return 4;
    };

    const svgNodes = graphNode
      .append("circle")
      .attr("class", nodeClass)
      .attr("fill", nodeFill)
      .attr("id", (d) => d.id)
      .attr("r", nodeRadius)
      .style("cursor", "pointer")
      .on("click", (event, node) => {
        router.push(`/c?url=${node.url}`);
      })
      .on("mouseover", function (event, node) {
        const neighbors = d3
          .selectAll<HTMLElement, NodeData>(`.graph-node`)
          .filter((d) => d.id !== node.id);
        const linkNodes = d3.selectAll(".graph-link").filter((d: LinkDatum) => {
          return d.source.id === node.id || d.target.id === node.id;
        }); // TODO: Only select links that are connected to this node
        const label = boundingBox.select(`#${getLabelId(node.id)}`);

        label.transition().duration(200).style("opacity", 1);

        // Highlight the links
        linkNodes.transition().duration(200).attr("stroke", activeLinkColor);
      })
      .on("mouseout", function (event, node) {
        const linkNodes = d3.selectAll(".graph-link"); // TODO: Only select links that are connected to this node
        const label = boundingBox.select(`#${getLabelId(node.id)}`);

        label.transition().duration(200).style("opacity", initialOpacity);

        // Return the links to normal
        linkNodes
          .transition()
          .duration(200)
          .attr("stroke", defaultLinkColor)
          .attr("stroke-width", 1);
      })
      .call(drag(simulation));

    // draw labels
    const labels = graphNode
      .append("text")
      .attr("dx", 0)
      .attr("dy", (d) => -nodeRadius(d) + "px")
      .attr("text-anchor", "middle")
      .text((d) => d.title)
      .attr("id", (d) => getLabelId(d.id))
      .style("opacity", initialOpacity)
      .style("pointer-events", "none")
      .style("font-size", localGraph.fontSize + "em")
      .raise()
      // @ts-ignore
      .call(drag(simulation));

    // progress the simulation
    simulation.on("tick", () => {
      // Draw the links
      svgLinks
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      svgNodes.attr("cx", (d: NodeData) => d.x).attr("cy", (d: any) => d.y);
      labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });
  };

  useEffect(() => {
    if (didInit) {
      return;
    }
    renderGraph();
    didInit = true;
  }, []);
};
