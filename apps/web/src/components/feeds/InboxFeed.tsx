"use client";
import { useInbox } from "@/api/hooks";
import { Feed, LoadingFeed } from "../Feed";

interface Props {
  userId: string;
}

export const InboxFeed = ({ userId }: Props) => {
  const { data, isLoading } = useInbox(userId);

  if (isLoading) {
    return <LoadingFeed />;
  }

  return (
    <div>
      <Feed feed={data} />
    </div>
  );
};
