"use client";
import { NetworkGraph } from "@/components/NetworkGraph";
import { GraphType } from "@/hooks/useGraph";

export default function Page() {
  return (
    <div>
      <NetworkGraph graphType={GraphType.GLOBAL} />
    </div>
  );
}
