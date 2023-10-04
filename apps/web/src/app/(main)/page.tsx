import { fetchSocialFeed } from "@/api";
import { SocialFeed } from "@/components/SocialFeed";

export default async function Home() {
  const feed = await fetchSocialFeed();

  return <SocialFeed feed={feed} />;
}
