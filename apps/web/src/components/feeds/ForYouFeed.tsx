"use client";
import { useForYou } from "@/api/hooks";
import { Feed, LoadingFeed } from "../Feed";

interface Props {
  userId: string;
}

export const ForYouFeed = ({ userId }: Props) => {
  const { data, isLoading } = useForYou(userId);

  if (isLoading) {
    return <LoadingFeed />;
  }

  return (
    <div>
      <Feed feed={data} />
    </div>
  );
};
