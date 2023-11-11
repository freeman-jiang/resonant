"use client";
import { PageNode } from "@/api";
import { renderGraph } from "@/app/d3/renderGraph";
import { useEffect } from "react";

interface Props {
  node: PageNode;
  neighbors: PageNode[];
}

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application
let didInit = false;

export function LocalGraph({ node, neighbors }: Props) {
  useEffect(() => {
    if (didInit) {
      return;
    }
    renderGraph(graphId, node, neighbors);
    didInit = true;
  }, []);

  return (
    <div>
      <div id={graphId} />
    </div>
  );
}
