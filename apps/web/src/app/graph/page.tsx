"use client";
import { NetworkGraph } from "@/components/NetworkGraph";

export default function Page() {
  // const { data } = useNetwork("https://hypertext.joodaloop.com/", 6);

  // if (!data) return <div>Loading...</div>;

  return (
    <div>
      <NetworkGraph />
    </div>
  );
}
