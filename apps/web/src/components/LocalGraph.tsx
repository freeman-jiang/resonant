"use client";
import { PageNodesResponse } from "@/api";
import { useGraph } from "@/hooks/useGraph";

interface Props {
  data: PageNodesResponse;
}

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application

export function LocalGraph({ data }: Props) {
  const { showLabels, setShowLabels } = useGraph(graphId, data);

  return (
    <div className="mt-4">
      <div className="text-lg font-semibold">Link Graph</div>
      <div className="h-60 border border-slate-200" id={graphId} />
    </div>
  );
}
