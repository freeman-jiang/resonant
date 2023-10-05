"use client";

import { extractDomain, formatExercept, getRelativeTime } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { Page } from "@/types/api";
import NextLink from "next/link";
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
    const avatars = senders.map((sender) => {
      const initials = `${sender.first_name[0]}${sender.last_name[0]}`;

      return (
        <TooltipProvider delayDuration={0} key={sender.id}>
          <Tooltip>
            <TooltipTrigger className="cursor-default">
              <Avatar className="h-6 w-6">
                <AvatarImage src={sender.profile_picture_url} />
                <AvatarFallback className="text-xs">{initials}</AvatarFallback>
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

  const Broadcast = () => {
    if (senders.length === 0) {
      return null;
    }
    return (
      <div className="text-xs text-slate-500">
        <div className="flex items-center ">
          {/* <span className="mr-2">Broadcasted by:</span> */}
          {renderAvatars()}
          <span className="ml-2">
            {getRelativeTime(mostRecentSender.sent_on)}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <Broadcast />
        <div className="flex flex-row items-center justify-between">
          <NextLink href={`/c?url=${page.url}`} className="cursor-pointer">
            <h2 className="text-xl font-semibold tracking-tight text-slate-900">
              {page.title || page.url}
            </h2>
            <p className="text-sm font-light text-slate-700">
              {extractDomain(page.url)}
            </p>
          </NextLink>
          <div className="ml-8 flex items-center lg:ml-20">
            <FeedbackButton
              page={page}
              canUnsend={canUnsend}
              className="ml-2"
            />
          </div>
        </div>
        <p className="mt-2 font-mono text-sm text-slate-500">
          {formatExercept(page.excerpt)}
        </p>
      </div>
    </div>
  );
};
