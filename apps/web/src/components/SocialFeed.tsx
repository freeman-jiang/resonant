import { FeedResponse, Message } from "@/api";
import { extractDomain, formatExercept } from "@/lib/utils";
import NextLink from "next/link";
import { Feed } from "./Feed";
import { FeedbackButton } from "./FeedbackButton";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";

export const Entry = (message: Message) => {
  const page = message.page;
  const { sender } = message;
  const name = `${sender.first_name} ${sender.last_name}`;
  const initials = `${sender.first_name[0]}${sender.last_name[0]}`;

  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="text-xs text-slate-500">
          Shared by: <span>{name}</span>
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
          <div className="ml-8 flex items-center gap-3 lg:ml-20">
            <Avatar className="h-6 w-6">
              <AvatarImage src={message.sender.profile_picture_url} />
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
            <FeedbackButton page={page} />
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

export const SocialFeed = ({ feed }: Props) => {
  return (
    <div className="mt-5 space-y-2">
      {feed.messages.map((message) => (
        <Entry {...message} key={`${message.page.url}-${message.sender.id}`} />
      ))}
      <Feed feed={feed.random_feed} />
    </div>
  );
};
