import { FEED_QUERY_KEY, useFeed } from "@/api/hooks";
import { useState } from "react";
import { Badge } from "./ui/badge";

enum Topic {
  Software,
  Climate,
  Philosophy,
  Politics,
  Science,
}

const TOPIC_LIST = Object.keys(Topic).filter((key) => isNaN(Number(key))); // filter out the numeric keys
const ALL = "All";

export const Topics = () => {
  const { refetch } = useFeed();
  const [currentTopic, setCurrentTopic] = useState<string>(ALL);
  const searchTopic = async (topic: string) => {
    await refetch({ queryKey: [FEED_QUERY_KEY, topic] });
  };

  return (
    <div className="mt-3 flex flex-row flex-wrap gap-2 pb-2">
      <Badge
        className="cursor-pointer text-sm"
        onClick={async () => {
          refetch();
          setCurrentTopic(ALL);
        }}
        variant={currentTopic === ALL ? "default" : "outline"}
      >
        All
      </Badge>
      {TOPIC_LIST.map((topic) => (
        <Badge
          key={topic}
          className="cursor-pointer text-sm"
          variant={currentTopic === topic ? "default" : "outline"}
          onClick={async () => {
            await searchTopic(topic);
            setCurrentTopic(topic);
          }}
        >
          {topic}
        </Badge>
      ))}
    </div>
  );
};
