"use client";
import { useRandomFeed } from "@/api/hooks";
import { Feed, LoadingFeed } from "./Feed";

export const RandomFeed = () => {
  const { data: randomFeed } = useRandomFeed();

  if (!randomFeed) {
    return <LoadingFeed />;
  }
  return <Feed feed={randomFeed} />;
};
