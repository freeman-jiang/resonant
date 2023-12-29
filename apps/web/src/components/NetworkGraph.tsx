"use client";
import { GraphType, useGraph } from "@/hooks/useGraph";

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application

interface Props {
  graphType: GraphType;
}

export function NetworkGraph({ graphType }: Props) {
  useGraph(graphId, null, graphType);

  return <div className="border border-slate-200" id={graphId} />;
}
