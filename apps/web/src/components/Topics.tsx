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
  Politics: "politics",
  Science: "science",
};

export const Topics = () => {
  const { topic } = useParams();
  const path = usePathname();
  const { session } = useSupabase();

  const renderTopics = () => {
    // Limit to 3 if signed in
    let topicsToRender = Object.entries(topics);
    if (session) {
      topicsToRender = topicsToRender.slice(0, 3);
    }
    return topicsToRender.map(([badgeTopic, prompt]) => (
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
    ));
  };

  return (
    <div className="mt-3 flex flex-row flex-wrap gap-2 pb-2">
      <NextLink href={"/"} onClick={() => trackClickTopic("For You")}>
        <Badge
          className="cursor-pointer text-sm"
          variant={!topic && path === "/" ? "default" : "outline"}
        >
          {session ? "For You" : "All"}
        </Badge>
      </NextLink>
      {session && (
        <>
          <NextLink href={"/inbox"} onClick={() => trackClickTopic("All")}>
            <Badge
              className="cursor-pointer text-sm"
              variant={!topic && path === "/inbox" ? "default" : "outline"}
            >
              Inbox
            </Badge>
          </NextLink>
          <NextLink href={"/all"} onClick={() => trackClickTopic("All")}>
            <Badge
              className="cursor-pointer text-sm"
              variant={!topic && path === "/all" ? "default" : "outline"}
            >
              All
            </Badge>
          </NextLink>
        </>
      )}
      <NextLink href={"/random"} onClick={() => trackClickTopic("Random")}>
        <Badge
          className="cursor-pointer text-sm"
          variant={!topic && path === "/random" ? "default" : "outline"}
        >
          Random
        </Badge>
      </NextLink>
      {renderTopics()}
    </div>
  );
};
