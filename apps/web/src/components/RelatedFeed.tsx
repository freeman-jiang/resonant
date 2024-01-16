"use client";
import { useSearch } from "@/api/hooks";
import { Feed } from "./Feed";

interface Props {
  url: string;
}

export const RelatedFeed = ({ url }: Props) => {
  const { data } = useSearch(url);

  return (
    <div className="mt-5">
      <h2 className="text-2xl font-semibold text-slate-900">Similar</h2>
      <Feed feed={data} />;
    </div>
  );
};
