// Heavily inspired by the Quartz graph view
import { LinkData, NodePage, PageNodesResponse } from "@/api";
import * as d3 from "d3";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

// graph.json is in the public folder
// @ts-ignore
import graphdata from "public/graph.json";
const globalGraphData = graphdata as PageNodesResponse;

type NodeData = NodePage & d3.SimulationNodeDatum;

type LinkDatum = {
  index: 0;
  source: NodeData;
  target: NodeData;
  // type: "inbound" | "outbound";
};

const old = {
  drag: true,
  zoom: true,
  depth: 1,
  scale: 1,
  repelForce: 1,
  centerForce: 0.3,
  linkDistance: 100,
  fontSize: 0.6,
  opacityScale: 2.5,
  showTags: true,
  removeTags: [],
};

const localGraph = {
  scale: 1,
  linkDistance: 100,
  fontSize: 0.6,
};

const defaultLinkColor = "#d8dee9"; // grey
const inboundLinkColor = "#f56565"; // red
const outboundLinkColor = "#38bdf8"; // blue
const activeLinkColor = "#5b7cab";
const defaultNodeColor = "#34d399"; // green
const activeNodeColor = "#38d5f5"; // bright blue
const GRAPH_SVG_ID = "graph-svg";

const getLabelId = (id: number) => `labelfor-${id}`;

// Expects there to be an empty div with the given id
export const useGraph = (id: string, data: PageNodesResponse | null) => {
  const isGlobalGraph = !data;
  const [showLabels, setShowLabels] = useState(!isGlobalGraph);
  const router = useRouter();

  const renderGraph = () => {
    const graph = document.getElementById(id);

    const graphData = data || globalGraphData;
    const rootUrl = graphData.root_url;

    const simulation: d3.Simulation<NodeData, LinkData> = d3
      .forceSimulation(graphData.nodes as NodeData[])
      .force(
        "link",
        d3
          .forceLink(graphData.links)
          .id((d: NodeData) => d.url) // custom id accessor
          .distance(localGraph.linkDistance),
      )
      .force(
        "charge",
        d3.forceManyBody().strength((d) => {
          // TODO: Make strength as a function of the number of links
          const base = -30;
          const multiplier = -5;

          return base;
        }),
      )
      .force("center", d3.forceCenter());

    const calculateHeight = () => {
      if (!isGlobalGraph) {
        return graph.offsetHeight;
      }

      const navbarHeight = document.getElementById("navbar").offsetHeight;
      return window.innerHeight - navbarHeight;
    };

    const width = graph.offsetWidth;
    const height = calculateHeight();

    const initialScale = isGlobalGraph ? 0.3 : 1;

    const boundingBox = d3
      .select<HTMLElement, NodeData>(`#${id}`)
      .append("svg")
      .attr("id", GRAPH_SVG_ID)
      // .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [
        -width / 2 / initialScale,
        -height / 2 / initialScale,
        width / initialScale,
        height / initialScale,
      ]);
    // .attr("class", "bg-black");

    // draw links between nodes
    const svgLinks = boundingBox
      .append("g")
      .selectAll("line")
      .data(graphData.links)
      .join("line")
      .attr("class", "graph-link")
      .attr(
        "stroke",
        (d) => defaultLinkColor,
        // d.type === "inbound" ? inboundLinkColor : outboundLinkColor,
      )
      .attr("stroke-width", 1);

    // Container for all the nodes
    const graphNode = boundingBox
      .append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .enter();

    const drag = (simulation: d3.Simulation<NodeData, LinkData>) => {
      // Reheat the simulation when drag starts, and fix the subject position.
      function dragstarted(event) {
        handleMouseover(event, event.subject);
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }

      // Update the subject (dragged node) position during drag.
      function dragged(event) {
        handleMouseover(event, event.subject);
        // Set cursor to grabbing
        // handleMouseover(event, event.subject);
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }

      // Restore the target alpha so the simulation cools after dragging ends.
      // Unfix the subject position now that it’s no longer being dragged.
      function dragended(event) {
        handleMouseout(event, event.subject);
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }

      return d3
        .drag<Element, NodeData>()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    };

    // calculate color
    const nodeClass = (d: NodeData): string => {
      const isCurrent = d.url === rootUrl;
      if (isCurrent) {
        return "graph-node-current";
      }
      return "graph-node";
    };

    // calculate node fill color
    const nodeFill = (d: NodeData): string => {
      const isCurrent = d.url === rootUrl;
      if (isCurrent) {
        return activeNodeColor;
      }
      return defaultNodeColor;
    };

    const nodeRadius = (d: NodeData): number => {
      // Determine radius based on number of links that node has
      const baseRadius = 5;
      const multiplier = 0.15;
      // const numLinks = Array.from(
      //   new Set(
      //     adjacencyList[d.url].outboundUrls.filter((url) => {
      //       return !!adjacencyList[url];
      //     }),
      //   ),
      // ).length;

      return baseRadius;
    };

    const getInitialOpacity = (n: NodeData) => {
      if (!showLabels) {
        return 0;
      }

      const isCurrent = n.url === rootUrl;
      if (isCurrent) {
        return 0.3;
      }
      return 0.15;
    };

    const getHoverNodes = (
      node: NodeData,
      directLinks: d3.Selection<HTMLElement, LinkDatum, HTMLElement, any>,
    ) => {
      // Adjacent to the root `node`
      const directNodeIds = new Set();
      directLinks.each((d) => {
        directNodeIds.add(d.source.id);
        directNodeIds.add(d.target.id);
      });

      // Select all nodes, and then filter out the connected nodes
      const otherNodes = d3.selectAll(".graph-node").filter((d: NodeData) => {
        return !directNodeIds.has(d.id);
      });

      const directNodes = d3.selectAll(".graph-node").filter((d: NodeData) => {
        return directNodeIds.has(d.id);
      });

      // Get labels
      const directLabels = labels.filter((d) => directNodeIds.has(d.id));

      const otherLabels = labels.filter((d) => !directNodeIds.has(d.id));

      return { otherNodes, directNodes, directLabels, otherLabels };
    };

    function handleMouseover(event: MouseEvent, node: NodeData) {
      const directLinks = d3
        .selectAll<HTMLElement, LinkDatum>(".graph-link")
        .filter((d) => {
          return d.source.id === node.id || d.target.id === node.id;
        });
      // const otherLinks = d3
      //   .selectAll<HTMLElement, LinkDatum>(".graph-link")
      //   .filter((d: LinkDatum) => {
      //     return d.source.id !== node.id && d.target.id !== node.id;
      //   });
      const { otherNodes, directLabels, otherLabels } = getHoverNodes(
        node,
        directLinks,
      );

      // // Dim all other nodes and links
      // const dimOpacity = 0.4;
      // otherNodes.transition().duration(300).style("opacity", dimOpacity);
      // otherLinks.transition().duration(300).style("opacity", dimOpacity);

      // // Highlight the node's immediate links
      directLinks.transition().duration(300).attr("stroke", activeLinkColor);

      // // Highlight direct labels
      directLabels.transition().duration(300).style("opacity", 0.5);
      otherLabels.transition().duration(300).style("opacity", 0.05);

      // // Highlight the label
      // const label = boundingBox.select(`#${getLabelId(node.id)}`);
      // label.transition().duration(300).style("opacity", 1);
    }

    const handleMouseout = (event: MouseEvent, node: NodeData) => {
      const directLinks = d3
        .selectAll<HTMLElement, LinkDatum>(".graph-link")
        .filter((d) => {
          return d.source.id === node.id || d.target.id === node.id;
        });
      const otherLinks = d3
        .selectAll<HTMLElement, LinkDatum>(".graph-link")
        .filter((d: LinkDatum) => {
          return d.source.id !== node.id && d.target.id !== node.id;
        });
      const { otherNodes, directLabels, otherLabels } = getHoverNodes(
        node,
        directLinks,
      );

      // Undim all other nodes and links
      otherNodes.transition().duration(300).style("opacity", 1);
      otherLinks.transition().duration(300).style("opacity", 1);

      // Unhighlight the node's immediate links
      directLinks
        .transition()
        .duration(300)
        .attr("stroke", (d: LinkDatum) => {
          return defaultLinkColor;
        });

      // Revert labels
      directLabels
        .transition()
        .duration(300)
        .style("opacity", (d) => getInitialOpacity(d));
      otherLabels
        .transition()
        .duration(300)
        .style("opacity", (d) => getInitialOpacity(d));

      // Unhighlight the label
      const label = boundingBox.select(`#${getLabelId(node.id)}`);
      label
        .transition()
        .duration(300)
        .style("opacity", getInitialOpacity(node));
    };

    const handleClick = (event: MouseEvent, node: NodeData) => {
      router.push(`/c?url=${node.url}`);
    };

    // draw labels
    const labels = graphNode
      .append("text")
      .attr("class", "graph-label")
      .attr("dx", 0)
      .attr("dy", (d) => nodeRadius(d) + 10)
      .attr("text-anchor", "middle")
      .text((d) => d.title)
      .attr("id", (d) => getLabelId(d.id))
      .style("opacity", getInitialOpacity)
      .style("font-size", localGraph.fontSize + "em")
      .style("background-color", "red");
    // .style("cursor", "pointer")
    // .on("click", handleClick)
    // .on("mouseover", handleMouseover)
    // .on("mouseout", handleMouseout)
    // .raise()
    // @ts-ignore
    // .call(drag(simulation));

    const svgNodes = graphNode
      .append("circle")
      .attr("class", nodeClass)
      .attr("fill", nodeFill)
      .attr("id", (d) => d.id)
      .attr("r", nodeRadius)
      .style("cursor", "pointer")
      .on("click", handleClick)
      .on("mouseover", handleMouseover)
      .on("mouseout", handleMouseout)
      .call(drag(simulation));

    boundingBox.call(
      d3
        .zoom<SVGSVGElement, NodeData>()
        .extent([
          [500, 500],
          [width, height],
        ])
        .scaleExtent([0.05, 2])
        .on("zoom", ({ transform }: any) => {
          svgLinks.attr("transform", transform);
          svgNodes.attr("transform", transform);
          labels.attr("transform", transform);
          // const scaledOpacity = transform.k * 0.2;
          // labels.attr("transform", transform).style("opacity", scaledOpacity);
        }),
    );

    // progress the simulation
    simulation.on("tick", () => {
      // Draw the links
      svgLinks
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      svgNodes.attr("cx", (d: NodeData) => d.x).attr("cy", (d: any) => d.y);
      labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });
  };

  useEffect(() => {
    // Check if the graph already exists
    const existingGraph = document.getElementById(GRAPH_SVG_ID);
    if (!existingGraph) {
      renderGraph();
    }

    return () => {
      const existingGraph = document.getElementById(GRAPH_SVG_ID);
      if (existingGraph) {
        existingGraph.remove();
      }
    };
  }, [id, data]);

  return { showLabels, setShowLabels };
};
