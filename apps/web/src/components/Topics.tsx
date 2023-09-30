"use client";
import NextLink from "next/link";
import { useParams } from "next/navigation";
import { Badge } from "./ui/badge";

const topics = {
  Software: "software engineering",
  Climate: "climate change",
  Philosophy: "philosophy",
  Politics: "politics",
  Science: "science",
};

export const Topics = () => {
  const { topic } = useParams();

  return (
    <div className="mt-3 flex flex-row flex-wrap gap-2 pb-2">
      <NextLink href={"/"}>
        <Badge
          className="cursor-pointer text-sm"
          variant={!topic ? "default" : "outline"}
        >
          All
        </Badge>
      </NextLink>
      {Object.entries(topics).map(([badgeTopic, prompt]) => (
        <NextLink key={badgeTopic} href={`/topic/${badgeTopic.toLowerCase()}`}>
          <Badge
            className="cursor-pointer text-sm"
            variant={topic === badgeTopic.toLowerCase() ? "default" : "outline"}
          >
            {badgeTopic}
          </Badge>
        </NextLink>
      ))}
    </div>
  );
};
