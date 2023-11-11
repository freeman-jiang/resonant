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

type SVGLinkData = d3.SimulationLinkDatum<NodeData>;

const localGraph = {
  drag: true,
  zoom: true,
  depth: 1,
  scale: 1.1,
  repelForce: 0.5,
  centerForce: 0.3,
  linkDistance: 70,
  fontSize: 0.6,
  opacityScale: 2.5,
  showTags: true,
  removeTags: [],
};

let didInit = false;

export const useGraph = (id: string, node: PageNode, neighbors: PageNode[]) => {
  const router = useRouter();

  const renderGraph = () => {
    const graph = document.getElementById(id);
    const links: LinkData[] = [];

    for (const neighbor of neighbors) {
      links.push({ source: node.url, target: neighbor.url });
    }

    const nodes: NodeData[] = [node, ...neighbors].map((node) => {
      return { ...node, title: node.title };
    });

    console.log(nodes);

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
      .attr("class", "stroke-slate-500 graph-link")
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
      const isCurrent = d.url === node.url;
      if (isCurrent) {
        return "fill-emerald-500 graph-node-current";
      }
      return "fill-slate-500 graph-node";
    };

    const nodeRadius = (d: NodeData): number => {
      const isCurrent = d.url === node.url;
      if (isCurrent) {
        return 4;
      }
      return 4;
    };

    const svgNodes = graphNode
      .append("circle")
      .attr("class", nodeClass)
      .attr("id", (d) => d.id)
      .attr("r", nodeRadius)
      .style("cursor", "pointer")
      .on("click", (event, node) => {
        router.push(`/c?url=${node.url}`);
      })
      .on("mouseover", function (event, node) {
        const neighbors = d3.selectAll<HTMLElement, NodeData>(`.graph-node`);
        const links = d3.selectAll<HTMLElement, SVGLinkData>(`.graph-link`);

        // FIXME: Not working
        // Highlight the neighbors and links
        neighbors.transition().duration(200).attr("fill", "red");

        // Highlight the links
        links
          .transition()
          .duration(200)
          .attr("stroke", "red")
          .attr("stroke-width", 1);

        // FIXME: Not working
        // show text for self
        d3.select("text ")
          .transition()
          .duration(200)
          // .attr("opacity", d3.select(parent).select("text").style("opacity"))
          .style("opacity", 1)
          .style("font-size", "0.75rem");
      })
      .call(drag(simulation));

    // draw labels
    const labels = graphNode
      .append("text")
      .attr("dx", 0)
      .attr("dy", (d) => -nodeRadius(d) + "px")
      .attr("text-anchor", "middle")
      .text((d) => d.title)
      .style("opacity", (localGraph.opacityScale - 1) / 3.75)
      .style("pointer-events", "none")
      .style("font-size", localGraph.fontSize + "em")
      .raise()
      // @ts-ignore
      .call(drag(simulation));

    // progress the simulation
    simulation.on("tick", () => {
      // Draw the links
      svgLinks
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      svgNodes.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
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
