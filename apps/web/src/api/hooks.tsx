import { Link } from "@/types/api";
import {
  HydrationBoundary,
  QueryClient,
  dehydrate,
  useQuery,
} from "@tanstack/react-query";
import { fetchFeed, searchFor } from ".";

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

export const FeedBoundary = async ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: [FEED_QUERY_KEY],
    queryFn: fetchFeed,
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

const SEARCH_QUERY_KEY = "search";

export const useSearch = (query: string) => {
  return useQuery({
    queryKey: [SEARCH_QUERY_KEY, query],
    queryFn: () => searchFor(query),
    refetchOnWindowFocus: false,
  });
};

interface SearchBoundaryProps {
  query: string;
  children: React.ReactNode;
}
export const SearchBoundary = async ({
  children,
  query,
}: SearchBoundaryProps) => {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: [SEARCH_QUERY_KEY, query],
    queryFn: () => searchFor(query),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};