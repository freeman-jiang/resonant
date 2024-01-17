"use client";
import { useForYou } from "@/api/hooks";
import { ZapOff } from "lucide-react";
import { Feed, LoadingFeed } from "../Feed";

interface Props {
  userId: string;
}

export const ForYouFeed = ({ userId }: Props) => {
  const { data, isLoading } = useForYou(userId);

  if (isLoading) {
    return <LoadingFeed />;
  }

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center">
        <ZapOff className="mt-6 block h-10 w-10 text-slate-600" />
        <div className="mt-8 text-center text-base text-slate-600">
          <div>{"Looks like there's nothing here :("}</div>
          <div>Try liking some articles to get recommendations.</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Feed feed={data} />
    </div>
  );
};
