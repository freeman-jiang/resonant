"use client";
import { trackClickTopic } from "@/analytics/mixpanel";
import { useSupabase } from "@/supabase/client";
import NextLink from "next/link";
import { useParams, usePathname } from "next/navigation";
import { Badge } from "./ui/badge";

const topics = {
  Software: "software engineering",
  Climate: "climate change",
  Philosophy: "philosophy",
  // Politics: "politics",
  // Science: "science",
};

export const Topics = () => {
  const { topic } = useParams();
  const path = usePathname();
  const { session } = useSupabase();

  return (
    <div className="mt-3 flex flex-row flex-wrap gap-2 pb-2">
      {session && (
        <NextLink href={"/"} onClick={() => trackClickTopic("For You")}>
          <Badge
            className="cursor-pointer text-sm"
            variant={!topic && path === "/" ? "default" : "outline"}
          >
            For You
          </Badge>
        </NextLink>
      )}
      <NextLink href={"/all"} onClick={() => trackClickTopic("All")}>
        <Badge
          className="cursor-pointer text-sm"
          variant={!topic && path === "/all" ? "default" : "outline"}
        >
          All
        </Badge>
      </NextLink>
      <NextLink href={"/random"} onClick={() => trackClickTopic("Random")}>
        <Badge
          className="cursor-pointer text-sm"
          variant={!topic && path === "/random" ? "default" : "outline"}
        >
          Random
        </Badge>
      </NextLink>
      <NextLink
        href={"/recommended"}
        onClick={() => trackClickTopic("Recommended")}
      >
        <Badge
          className="cursor-pointer text-sm"
          variant={!topic && path === "/recommended" ? "default" : "outline"}
        >
          Recommended
        </Badge>
      </NextLink>
      {Object.entries(topics).map(([badgeTopic, prompt]) => (
        <NextLink
          key={badgeTopic}
          href={`/topic/${badgeTopic.toLowerCase()}`}
          onClick={() => trackClickTopic(badgeTopic)}
        >
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
