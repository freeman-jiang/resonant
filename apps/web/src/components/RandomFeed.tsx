"use client";
import { useRandomFeed } from "@/api/hooks";
import { Feed } from "./Feed";

export const RandomFeed = () => {
  const { data: randomFeed } = useRandomFeed();
  return <Feed feed={randomFeed} />;
};
