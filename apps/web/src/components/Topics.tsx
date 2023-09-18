import { fetchFeed, searchFor } from "@/api";
import { useFeed } from "@/context/FeedContext";
import { Badge } from "./ui/badge";

const TOPICS = ["Software", "Climate", "Philosophy"];

export const Topics = () => {
  const { setLinks } = useFeed();
  const searchTopic = async (topic: string) => {
    const data = await searchFor(topic);
    setLinks(data);
  };

  return (
    <div className="mt-3 flex flex-row gap-2 pb-2">
      <Badge
        className="cursor-pointer text-sm"
        onClick={async () => {
          const data = await fetchFeed();
          setLinks(data);
        }}
      >
        All
      </Badge>
      {TOPICS.map((topic) => (
        <Badge
          key={topic}
          className="cursor-pointer text-sm"
          variant="outline"
          onClick={() => searchTopic(topic)}
        >
          {topic}
        </Badge>
      ))}
    </div>
  );
};
