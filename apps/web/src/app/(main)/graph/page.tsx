"use client";
import { usePageNodes } from "@/api/hooks";
import { LocalGraph } from "@/components/LocalGraph";

export default function Page() {
  const { data } = usePageNodes(
    "https://www.cs.cornell.edu/~kt/post/site-graph/",
  );

  if (!data) {
    return <div>Loading...</div>;
  }

  const { neighbors, node } = data || {};
  // console.log(neighbors, node);

  return <LocalGraph node={node} neighbors={neighbors} />;
}
