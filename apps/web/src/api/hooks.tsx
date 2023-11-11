import { Session } from "@supabase/supabase-js";
import {
  HydrationBoundary,
  QueryClient,
  dehydrate,
  useQuery,
} from "@tanstack/react-query";
import { ReactNode } from "react";
import {
  Page,
  crawlUrl,
  fetchGlobalFeed,
  fetchInbox,
  fetchRandomFeed,
  fetchRecommendedFeed,
  findPage,
  getLikedPages,
  getPageNodes,
  getUser,
  getUserFeed,
  searchFor,
  searchUsers,
} from ".";

// TODO: Consider using SSR by making this a server component
export const GLOBAL_FEED_QUERY_KEY = "global-feed";

interface Options {
  initialData: Page[];
}

export const useGlobalFeed = (options?: Options) => {
  return useQuery({
    queryKey: [GLOBAL_FEED_QUERY_KEY],
    queryFn: fetchGlobalFeed,
  });
};

export const GlobalFeedBoundary = async ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const queryClient = new QueryClient();
  await queryClient.prefetchQuery({
    queryKey: [GLOBAL_FEED_QUERY_KEY],
    queryFn: fetchGlobalFeed,
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

  const requests = [
    queryClient.prefetchQuery({
      queryKey: [PAGE_QUERY_KEY, url],
      queryFn: () => findPage(url, session),
    }),
    queryClient.prefetchQuery({
      queryKey: [PAGE_NODES_KEY, url],
      queryFn: () => getPageNodes(url),
    }),
  ];

  await Promise.all(requests);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

export const PAGE_NODES_KEY = "page-nodes";

export const usePageNodes = (pageUrl: string) => {
  return useQuery({
    queryKey: [PAGE_NODES_KEY, pageUrl],
    queryFn: () => getPageNodes(pageUrl),
  });
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

export const LIKED_FEED_QUERY_KEY = "liked-feed";

export const useLikedFeed = (session: Session) => {
  return useQuery({
    queryKey: [LIKED_FEED_QUERY_KEY],
    queryFn: () => getLikedPages(session.user.id),
  });
};

interface LikedFeedBoundaryProps {
  children: React.ReactNode;
  session: Session;
}

export const LikedFeedBoundary = async ({
  children,
  session,
}: LikedFeedBoundaryProps) => {
  const queryClient = new QueryClient();

  await queryClient.prefetchQuery({
    queryKey: [LIKED_FEED_QUERY_KEY],
    queryFn: () => getLikedPages(session.user.id),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

export const CRAWL_QUERY_KEY = "crawl";

export const useCrawl = (url: string) => {
  return useQuery({
    queryKey: [CRAWL_QUERY_KEY, url],
    queryFn: () => crawlUrl(url),
    retry: false,
    staleTime: 0,
  });
};

export const USER_QUERY_KEY = "user";

export const useUser = (userId: string) => {
  return useQuery({
    queryKey: [USER_QUERY_KEY],
    queryFn: () => {
      return getUser(userId);
    },
    enabled: !!userId,
    staleTime: 3600,
  });
};

interface UserBoundaryProps {
  session: Session;
  children: React.ReactNode;
}

export const UserBoundary = async ({
  children,
  session,
}: UserBoundaryProps) => {
  const queryClient = new QueryClient();
  if (session) {
    await queryClient.prefetchQuery({
      queryKey: [USER_QUERY_KEY],
      queryFn: () => getUser(session.user.id),
    });
  }

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

export const USER_SEARCH_QUERY_KEY = "user-search";

export const useUserSearch = (query: string) => {
  return useQuery({
    queryKey: [USER_SEARCH_QUERY_KEY, query],
    queryFn: () => searchUsers(query),
    staleTime: Infinity,
  });
};

export const USER_FEED_QUERY_KEY = "user-feed";

export const useUserFeed = (userId: string) => {
  return useQuery({
    queryKey: [USER_FEED_QUERY_KEY, userId],
    queryFn: () => getUserFeed(userId),
  });
};

interface UserFeedBoundaryProps {
  userId: string;
  children: React.ReactNode;
}

export const UserFeedBoundary = async ({
  children,
  userId,
}: UserFeedBoundaryProps) => {
  const queryClient = new QueryClient();

  await queryClient.prefetchQuery({
    queryKey: [USER_FEED_QUERY_KEY, userId],
    queryFn: () => getUserFeed(userId),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

export const RANDOM_FEED_QUERY_KEY = "random-feed";

export const useRandomFeed = () => {
  return useQuery({
    queryKey: [RANDOM_FEED_QUERY_KEY],
    queryFn: () => fetchRandomFeed(),
  });
};

interface RandomFeedBoundaryProps {
  children: React.ReactNode;
}

export const RandomFeedBoundary = async ({
  children,
}: RandomFeedBoundaryProps) => {
  const queryClient = new QueryClient();

  await queryClient.prefetchQuery({
    queryKey: [RANDOM_FEED_QUERY_KEY],
    queryFn: () => fetchRandomFeed(),
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {children}
    </HydrationBoundary>
  );
};

export const RECOMMENDED_FEED_QUERY_KEY = "recommended-feed";

export const useRecommendedFeed = (userId: string) => {
  return useQuery({
    queryKey: [RECOMMENDED_FEED_QUERY_KEY],
    queryFn: () => fetchRecommendedFeed(userId),
  });
};

export const INBOX_QUERY_KEY = "inbox";

export const useInbox = (userId: string) => {
  return useQuery({
    queryKey: [INBOX_QUERY_KEY],
    queryFn: () => fetchInbox(userId),
  });
};
