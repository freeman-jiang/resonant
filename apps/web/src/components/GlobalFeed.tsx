"use client";

import { useGlobalFeed } from "@/api/hooks";
import { Entry } from "./Entry";
import { Feed } from "./Feed";

export const GlobalFeed = () => {
  const { data: feed } = useGlobalFeed();

  return (
    <div className="space-y-2">
      {feed.messages.map((message) => {
        const senderIds = message.senders.map((sender) => sender.id).join(", ");
        return <Entry {...message} key={`${message.url}-${senderIds}`} />;
      })}
      <Feed feed={feed.random_feed} />
    </div>
  );
};