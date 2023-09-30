import { fetchFeed } from "@/api";
import { Feed } from "@/components/Feed";
import { Search } from "@/components/Search";

export default async function Home() {
  const feed = await fetchFeed();

  return (
    <div>
      {/* TODO: Add back topics */}
      <Search />
      <Feed feed={feed} />
    </div>
  );
}
