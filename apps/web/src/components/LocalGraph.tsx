"use client";
import { PageNodesResponse } from "@/api";
import { useGraph } from "@/app/hooks/useGraph";

interface Props {
  data: PageNodesResponse;
}

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application

export function LocalGraph({ data }: Props) {
  useGraph(graphId, data);

  return (
    <div className="mt-3">
      <div className="text-lg font-medium">Graph View</div>
      <div className="border border-slate-200" id={graphId} />
    </div>
  );
}
