"use client";
import { trackClickOutboundLink, trackClickPage } from "@/analytics/mixpanel";
import { Page, unlikePage } from "@/api";
import { LIKED_FEED_QUERY_KEY, useLikedFeed } from "@/api/hooks";
import { extractDomain, formatExcerpt } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { useQueryClient } from "@tanstack/react-query";
import { ExternalLink, MoreHorizontal, X } from "lucide-react";
import NextLink from "next/link";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface Props {
  feed: Page[];
}

export const Entry = (page: Page) => {
  const {
    session: { user },
  } = useSupabase();
  const queryClient = useQueryClient();

  const handleUnlike = async () => {
    await unlikePage(user.id, page.id);
    queryClient.invalidateQueries({ queryKey: [LIKED_FEED_QUERY_KEY] });
  };

  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="flex flex-row justify-between">
          <NextLink
            href={`/c?url=${page.url}`}
            onClick={() => trackClickPage(page.url)}
            className="cursor-pointer"
          >
            <h2 className="text-xl font-semibold tracking-tight text-slate-900">
              {page.title || page.url}
            </h2>
            <p className="text-sm font-light text-slate-700">
              {extractDomain(page.url)}
            </p>
          </NextLink>
          <div className="ml-8 flex items-center gap-2 lg:ml-20">
            <NextLink
              href={page.url}
              target="_blank"
              onClick={() => trackClickOutboundLink(page.url)}
            >
              <ExternalLink className="-mt-1 h-4 w-4" />
            </NextLink>
            <div>
              <DropdownMenu>
                <DropdownMenuTrigger>
                  <div>
                    <span className="sr-only">
                      Give feedback on article relevancy
                    </span>
                    <MoreHorizontal className="h-4 w-4" />
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem
                    className="cursor-pointer gap-2"
                    onClick={handleUnlike}
                  >
                    <X className="h-4 w-4" /> Unlike this
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
        <p className="mt-2 break-all font-mono text-sm text-slate-500">
          {formatExcerpt(page.excerpt)}
        </p>
      </div>
    </div>
  );
};

export const LikedFeed = () => {
  const { session } = useSupabase();
  const { data: feed } = useLikedFeed(session);

  return (
    <div className="mt-5 space-y-2">
      {feed.map((page) => (
        <Entry {...page} key={page.url} />
      ))}
    </div>
  );
};
