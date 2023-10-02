"use client";

import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { amplitude } from "@/analytics/amplitude";
import { NEXT_PUBLIC_AMPLITUDE_API_KEY } from "@/config";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";

export function Providers({ children }) {
  useEffect(() => {
    if (!NEXT_PUBLIC_AMPLITUDE_API_KEY) {
      console.log("NEXT_PUBLIC_AMPLITUDE_API_KEY is not set");
      return;
    }
    amplitude.init(NEXT_PUBLIC_AMPLITUDE_API_KEY || "", {
      defaultTracking: {
        formInteractions: false,
        pageViews: true,
        sessions: true,
      },
    });
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
