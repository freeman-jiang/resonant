import { fetchFeed } from "@/api";
import { Feed } from "@/components/Feed";

export default async function Home() {
  const feed = await fetchFeed();

  return <Feed feed={feed} />;
}
