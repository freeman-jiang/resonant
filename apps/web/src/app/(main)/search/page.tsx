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
    <div>
      <div className="break-all font-mono">{q}</div>
      <Feed feed={data} />
    </div>
  );
};

export default Page;
