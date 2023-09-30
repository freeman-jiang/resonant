import { Search } from "@/components/Search";
import { SearchFeed } from "@/components/SearchFeed";

interface RouteParams {
  searchParams: {
    q: string;
  };
}

const Page = async (params: RouteParams) => {
  const { q } = params.searchParams;

  return (
    <div>
      <Search initialQuery={q} />
      <div className="mt-5">
        <div className="font-mono text-lg">{q}</div>
        <SearchFeed query={q} />
      </div>
    </div>
  );
};

export default Page;
