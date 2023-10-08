import { GlobalFeedBoundary } from "@/api/hooks";
import { GlobalFeed } from "@/components/GlobalFeed";

export default async function Home() {
  return (
    <GlobalFeedBoundary>
      <GlobalFeed />
    </GlobalFeedBoundary>
  );
}
