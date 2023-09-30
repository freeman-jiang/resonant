"use client";
import { useSearch } from "@/api/hooks";
import { Feed } from "@/components/Feed";

interface RouteParams {
  searchParams: {
    q: string;
  };
}

const Page = (params: RouteParams) => {
  const { q } = params.searchParams;
  const { data } = useSearch(q);

  return (
    <div className="mt-5">
      <div className="font-mono text-lg">{q}</div>
      <Feed feed={data} />
    </div>
  );
};

export default Page;
