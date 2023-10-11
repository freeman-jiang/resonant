"use client";

import { trackClickOutboundLink, trackClickPage } from "@/analytics/mixpanel";
import { Page } from "@/api";
import { extractDomain, formatExcerpt } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { FeedbackButton } from "./FeedbackButton";
import { LinkedBy } from "./LinkedBy";
import { Senders } from "./Senders";
export const Entry = (page: Page) => {
  const { senders } = page;
  const { session } = useSupabase();
  const user = session?.user;

  // Look if the current user's id is in the list of senders
  const canUnsend = user && senders.some((sender) => sender.id === user.id);

  const linkToRelated = `/c?url=${page.url}`;

  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="flex flex-row items-center justify-between">
          <Link
            href={linkToRelated}
            className="cursor-pointer"
            onClick={() => trackClickPage(page.url)}
          >
            <h2 className="text-xl font-semibold tracking-tight text-slate-900">
              {page.title || page.url}
            </h2>
            <p className="text-sm font-light text-slate-700">
              {extractDomain(page.url)}
            </p>
          </Link>
          <div className="ml-8 flex items-center lg:ml-20">
            <Link
              href={page.url}
              target="_blank"
              onClick={() => trackClickOutboundLink(page.url)}
            >
              <ExternalLink className="-mt-1 h-5 w-5" />
            </Link>
            <FeedbackButton
              page={page}
              canUnsend={canUnsend}
              className="ml-2"
            />
          </div>
        </div>
        <Link
          href={linkToRelated}
          onClick={() => trackClickOutboundLink(page.url)}
        >
          <p className="mt-2 break-all font-mono text-sm text-slate-500">
            {formatExcerpt(page.excerpt)}
          </p>
        </Link>
        <LinkedBy page={page} />
        <Senders senders={senders} />
      </div>
    </div>
  );
};
