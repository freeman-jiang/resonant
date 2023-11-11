"use client";
import { PageNode } from "@/api";
import { useGraph } from "@/app/hooks/useGraph";

interface Props {
  node: PageNode;
  neighbors: PageNode[];
}

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application
let didInit = false;

export function LocalGraph({ node, neighbors }: Props) {
  useGraph(graphId, node, neighbors);

  return (
    <div>
      <div id={graphId} />
    </div>
  );
}
