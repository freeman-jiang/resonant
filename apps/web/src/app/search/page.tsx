import { searchFor } from "@/api";
import { Entry } from "@/components/Entry";
import { LoadingFeed } from "@/components/Feed";
import { Suspense } from "react";

interface RouteParams {
  searchParams: {
    q: string;
  };
}

const Page = async (params: RouteParams) => {
  const { q } = params.searchParams;

  return (
    <div className="mt-5">
      <div className="font-mono text-lg">{q}</div>
      <Suspense fallback={<LoadingFeed />}>
        <SearchFeed q={q} />
      </Suspense>
    </div>
  );
};

interface Props {
  q: string;
}

const SearchFeed = async ({ q }: Props) => {
  const results = await searchFor(q);

  return (
    <div className="mt-5">
      {results.map((page) => (
        <Entry key={page.url} {...page} />
      ))}
    </div>
  );
};

export default Page;
