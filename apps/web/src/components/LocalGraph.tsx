"use client";
import { PageNode } from "@/api";
import { useGraph } from "@/app/hooks/useGraph";

interface Props {
  node: PageNode;
  neighbors: PageNode[];
}

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application

export function LocalGraph({ node, neighbors }: Props) {
  useGraph(graphId, node, neighbors);

  return (
    <div className="mt-3">
      <div className="text-lg font-medium">Graph View</div>
      <div className="border border-slate-200" id={graphId} />
    </div>
  );
}
