"use client";

import { NEXT_PUBLIC_MIXPANEL_PROJECT_TOKEN } from "@/config";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import mixpanel from "mixpanel-browser";
import { useEffect, useState } from "react";

export function Providers({ children }) {
  useEffect(() => {
    if (!NEXT_PUBLIC_MIXPANEL_PROJECT_TOKEN) {
      console.log("NEXT_PUBLIC_MIXPANEL_PROJECT_TOKEN is not set");
      return;
    }

    if (process.env.NODE_ENV === "production") {
      mixpanel.init(NEXT_PUBLIC_MIXPANEL_PROJECT_TOKEN, {
        track_pageview: true,
        persistence: "localStorage",
      });
    } else {
      mixpanel.init("NONE");
      mixpanel.disable();
    }
  }, []);

  const [queryClient] = useState(
    () =>
      new QueryClient({
        // defaultOptions: {
        //   queries: {
        //     // With SSR, we usually want to set some default staleTime
        //     // above 0 to avoid refetching immediately on the client
        //     staleTime: 60 * 1000,
        //   },
        // },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
