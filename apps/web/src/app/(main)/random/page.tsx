import { RandomFeedBoundary } from "@/api/hooks";
import { RandomFeed } from "@/components/RandomFeed";

export default async () => {
  return (
    <RandomFeedBoundary>
      <RandomFeed />
    </RandomFeedBoundary>
  );
};
