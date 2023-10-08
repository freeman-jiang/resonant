import { GlobalFeedBoundary } from "@/api/hooks";
import { GlobalFeed } from "@/components/GlobalFeed";

export default async () => {
  return (
    <GlobalFeedBoundary>
      <GlobalFeed />
    </GlobalFeedBoundary>
  );
};
