"use client";
import { useNetwork } from "@/api/hooks";
import { NetworkGraph } from "@/components/NetworkGraph";

export default function Page() {
  const { data } = useNetwork("https://hypertext.joodaloop.com/", 3);

  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <NetworkGraph data={data} />
    </div>
  );
}
