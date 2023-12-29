"use client";
import { useGraph } from "@/hooks/useGraph";

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application

export function NetworkGraph() {
  useGraph(graphId, null);

  return <div className="border border-slate-200" id={graphId} />;
}
