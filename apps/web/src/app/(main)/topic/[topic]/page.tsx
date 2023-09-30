"use client";
import { useSearch } from "@/api/hooks";
import { Feed } from "@/components/Feed";

interface Route {
  params: {
    topic: string;
  };
}

export default function Topic(route: Route) {
  const { topic } = route.params;
  const { data } = useSearch(topic);

  return <Feed feed={data} />;
}
