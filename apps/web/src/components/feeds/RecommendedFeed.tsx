"use client";
import { useRecommendedFeed } from "@/api/hooks";
import { Feed, LoadingFeed } from "../Feed";

interface Props {
  userId: string;
}

export const RecommendedFeed = ({ userId }: Props) => {
  const { data, isLoading } = useRecommendedFeed(userId);

  if (isLoading) {
    return <LoadingFeed />;
  }

  return (
    <div>
      <Feed feed={data} />
    </div>
  );
};
