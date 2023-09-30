"use client";
import { useSearch } from "@/api/hooks";
import { Entry } from "./Entry";
import { LoadingFeed } from "./Feed";

interface Props {
  url: string;
}

export const RelatedFeed = ({ url }: Props) => {
  const { data } = useSearch(url);

  if (!data) {
    return <LoadingFeed />;
  }

  return (
    <div className="mt-5 space-y-2">
      {data.map((page) => (
        <Entry key={page.url} {...page} />
      ))}
    </div>
  );
};
