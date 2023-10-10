"use client";

import { trackClickLink } from "@/analytics/amplitude";
import { Page } from "@/api";
import { extractDomain, formatExcerpt, getRelativeTime } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { ExternalLink } from "lucide-react";
import Link from "next/link";
import { Fragment } from "react";
import { FeedbackButton } from "./FeedbackButton";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
export const Entry = (page: Page) => {
  const { senders } = page;

  // Backend sends order descending for dates (most recent first)
  const mostRecentSender = senders.length > 0 ? senders[0] : null;

  // TODO: Limit number of avatars shown to have +X more
  const renderAvatars = () => {
    // Filter out duplicate senders
    // TODO: This should maybe probably be done on backend
    const senderIds = new Set();

    const avatars = senders
      .filter((sender) => {
        if (senderIds.has(sender.id)) {
          return false;
        }
        senderIds.add(sender.id);
        return true;
      })
      .map((sender) => {
        const initials = `${sender.first_name[0]}${sender.last_name[0]}`;

        return (
          <TooltipProvider delayDuration={0} key={sender.id}>
            <Tooltip>
              <TooltipTrigger className="cursor-default">
                <Avatar className="h-6 w-6">
                  <AvatarImage src={sender.profile_picture_url} />
                  <AvatarFallback className="text-xs">
                    {initials}
                  </AvatarFallback>
                </Avatar>
              </TooltipTrigger>
              <TooltipContent>
                <div className="text-slate-800">{`${sender.first_name} ${sender.last_name}`}</div>
                <div className="text-xs text-slate-500">
                  {getRelativeTime(sender.sent_on)}
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      });

    return <div className="flex -space-x-1.5">{avatars}</div>;
  };

  const { session } = useSupabase();
  const user = session?.user;

  // Look if the current user's id is in the list of senders
  const canUnsend = user && senders.some((sender) => sender.id === user.id);

  const SharedUsers = () => {
    if (senders.length === 0) {
      return null;
    }
    return (
      <div className="mt-2 text-xs text-slate-500">
        <div className="flex items-center ">
          {renderAvatars()}
          <span className="ml-2">
            Shared {getRelativeTime(mostRecentSender.sent_on)}
          </span>
        </div>
      </div>
    );
  };

  const LinkedBy = () => {
    if (page.linked_by.length === 0) {
      return null;
    }

    return (
      <div className="mt-2 text-xs text-slate-500">
        <span className="">Linked by: </span>
        {page.linked_by.map((url, index) => (
          <Fragment key={url}>
            <Link href={url} target="_blank" className="text-emerald-600">
              {extractDomain(url)}
            </Link>
            {index !== page.linked_by.length - 1 && ", "}
          </Fragment>
        ))}
      </div>
    );
  };

  const linkToRelated = `/c?url=${page.url}`;

  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="flex flex-row items-center justify-between">
          <Link href={linkToRelated} className="cursor-pointer">
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
              onClick={() => trackClickLink(page.url)}
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
        <Link href={linkToRelated}>
          <p className="mt-2 font-mono text-sm text-slate-500">
            {formatExcerpt(page.excerpt)}
          </p>
        </Link>
        <LinkedBy />
        <SharedUsers />
      </div>
    </div>
  );
};
