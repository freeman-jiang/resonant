import { fetchFeed, searchFor } from "@/api";
import { FEED_QUERY_KEY } from "@/api/hooks";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Badge } from "./ui/badge";

const topics = {
  Software: "software engineering",
  Climate: "climate change",
  Philosophy: "philosophy",
  Politics: "politics",
  Science: "science",
};

const ALL = "All";

export const Topics = () => {
  const queryClient = useQueryClient();
  const [currentTopic, setCurrentTopic] = useState<string>(ALL);
  const searchTopic = async (topic: string) => {
    const result = await searchFor(topic);
    queryClient.setQueryData([FEED_QUERY_KEY], result);
  };

  return (
    <div className="mt-3 flex flex-row flex-wrap gap-2 pb-2">
      <Badge
        className="cursor-pointer text-sm"
        onClick={async () => {
          const result = await fetchFeed();
          queryClient.setQueryData([FEED_QUERY_KEY], result);
          setCurrentTopic(ALL);
        }}
        variant={currentTopic === ALL ? "default" : "outline"}
      >
        All
      </Badge>
      {Object.entries(topics).map(([topic, prompt]) => (
        <Badge
          key={topic}
          className="cursor-pointer text-sm"
          variant={currentTopic === topic ? "default" : "outline"}
          onClick={async () => {
            await searchTopic(prompt);
            setCurrentTopic(topic);
          }}
        >
          {topic}
        </Badge>
      ))}
    </div>
  );
};
