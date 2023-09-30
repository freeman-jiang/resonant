"use client";
import { useSearch } from "@/api/hooks";
import { Feed } from "./Feed";

interface Props {
  url: string;
}

export const RelatedFeed = ({ url }: Props) => {
  const { data } = useSearch(url);

  return <Feed feed={data} />;
};
