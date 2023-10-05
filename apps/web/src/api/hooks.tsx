import { Page } from "@/types/api";
import { Session } from "@supabase/supabase-js";
import {
  HydrationBoundary,
  QueryClient,
  dehydrate,
  useQuery,
} from "@tanstack/react-query";
import { ReactNode } from "react";
import { fetchSocialFeed, findPage, searchFor } from ".";

// TODO: Consider using SSR by making this a server component
export const FEED_QUERY_KEY = "feed";

interface Options {
  initialData: Page[];
}

export const useFeed = (options?: Options) => {
  return useQuery({
    queryKey: [FEED_QUERY_KEY],
    queryFn: fetchSocialFeed,
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
    queryFn: fetchSocialFeed,
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

export const PAGE_QUERY_KEY = "page";

export const usePage = (url: string, session: Session) => {
  return useQuery({
    queryKey: [PAGE_QUERY_KEY, url],
    queryFn: () => findPage(url, session),
  });
};

interface PageBoundaryProps {
  children: ReactNode;
  url: string;
  session: Session;
}

export const PageBoundary = async ({
  children,
  session,
  url,
}: PageBoundaryProps) => {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: [PAGE_QUERY_KEY, url],
    queryFn: () => findPage(url, session),
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
