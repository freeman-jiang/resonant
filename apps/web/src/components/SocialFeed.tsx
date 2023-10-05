"use client";

import { FeedResponse, Message } from "@/api";
import { useFeed } from "@/api/hooks";
import { extractDomain, formatExercept } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import NextLink from "next/link";
import { Feed } from "./Feed";
import { FeedbackButton } from "./FeedbackButton";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";

export const Entry = (message: Message) => {
  const page = message.page;
  const { senders } = message;

  // TODO: Add multiple profile images shared in a stack with +3... more type

  const senderNames = senders.map(
    (sender) => `${sender.first_name} ${sender.last_name}`,
  );

  // Add commas between names
  const formatSenderNames = (names: string[]) => {
    const last = names.pop();
    if (names.length === 0) {
      return last;
    }
    return `${names.join(", ")} & ${last}`;
  };

  const renderAvatars = () => {
    const avatars = senders.map((sender) => {
      const initials = `${sender.first_name[0]}${sender.last_name[0]}`;

      return (
        <TooltipProvider delayDuration={0}>
          <Tooltip>
            <TooltipTrigger className="cursor-default">
              <Avatar key={sender.id} className="h-6 w-6">
                <AvatarImage src={sender.profile_picture_url} />
                <AvatarFallback className="text-xs">{initials}</AvatarFallback>
              </Avatar>
            </TooltipTrigger>
            <TooltipContent>
              {sender.first_name} {sender.last_name}
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

  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="text-xs text-slate-500">
          <div className="flex items-center ">
            <span className="mr-2">Broadcasted by:</span>
            {renderAvatars()}
          </div>
        </div>
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

interface Props {
  feed: FeedResponse;
}

export const SocialFeed = () => {
  const { data: feed } = useFeed();

  return (
    <div className="mt-5 space-y-2">
      {feed.messages.map((message) => (
        <Entry {...message} key={`${message.page.url}-${message.senders}`} />
      ))}
      <Feed feed={feed.random_feed} />
    </div>
  );
};
