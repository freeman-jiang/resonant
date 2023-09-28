import { Link } from "@/types/api";
import { useQuery } from "@tanstack/react-query";
import { fetchFeed } from ".";

// TODO: Consider using SSR by making this a server component
export const FEED_QUERY_KEY = "feed";

export const useFeed = (initialData?: Link[]) => {
  return useQuery({
    queryKey: [FEED_QUERY_KEY],
    queryFn: ({ queryKey }) => fetchFeed(),
    initialData,
  });
};
