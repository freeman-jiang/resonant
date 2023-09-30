"use client";
import { useSearch } from "@/api/hooks";
import { Entry } from "./Entry";
import { LoadingFeed } from "./Feed";

interface Props {
  query: string;
}

export const SearchFeed = ({ query }: Props) => {
  const { data, isLoading, isFetching } = useSearch(query);
  console.log(isLoading, isFetching);

  if (!data) {
    return <LoadingFeed />;
  }

  return (
    <div className="mt-5">
      {data.map((page) => (
        <Entry key={page.url} {...page} />
      ))}
    </div>
  );
};
