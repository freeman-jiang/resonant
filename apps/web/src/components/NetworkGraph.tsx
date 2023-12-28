"use client";
import { useGraph } from "@/hooks/useGraph";
import { useEffect } from "react";

const graphId = "graph";
// This is apparently actually idiomatic: https://react.dev/learn/you-might-not-need-an-effect#initializing-the-application

export function NetworkGraph() {
  useGraph(graphId, null);

  // lol hacky, supposedly theres a flexbox way to do this but eh
  useEffect(() => {
    // Find height of navbar with id="navbar"
    const navbarHeight = document.getElementById("navbar").offsetHeight;
    console.log(navbarHeight);

    // Set height of graph to height of window minus navbar height
    const graph = document.getElementById(graphId);
    graph.style.height = `${window.innerHeight - navbarHeight}px`;
  }, [graphId]);

  return <div className="border border-slate-200" id={graphId} />;
}
