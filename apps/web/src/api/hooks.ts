import { Link } from "@/types/api";
import { useQuery } from "@tanstack/react-query";
import { fetchFeed } from ".";

// TODO: Consider using SSR by making this a server component
export const FEED_QUERY_KEY = "feed";

interface Options {
  initialData: Link[];
}

export const useFeed = (options?: Options) => {
  return useQuery({
    queryKey: [FEED_QUERY_KEY],
    queryFn: fetchFeed,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
  });
};
