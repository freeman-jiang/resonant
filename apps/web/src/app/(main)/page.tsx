import { FeedBoundary } from "@/api/hooks";
import { SocialFeed } from "@/components/SocialFeed";

export default async function Home() {
  return (
    <FeedBoundary>
      <SocialFeed />
    </FeedBoundary>
  );
}
