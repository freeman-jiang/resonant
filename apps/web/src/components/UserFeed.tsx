"use client";

import { useUserFeed } from "@/api/hooks";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { Feed } from "./Feed";
import { buttonVariants } from "./ui/button";

interface Props {
  userId: string;
}

export const UserFeed = ({ userId }: Props) => {
  const { data: feed } = useUserFeed(userId);

  if (feed.length === 0) {
    return (
      <div className="text-slate-500">
        <div>Looks like no one has sent you anything yet.</div>
        <div>Find a link and send yourself something to get started!</div>
        <div className="mt-2">
          Or check out the global broadcasts{" "}
          <Link
            href={"/all"}
            className={cn(buttonVariants({ variant: "link" }), "p-0 text-base")}
          >
            here
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Feed feed={feed} />
    </div>
  );
};
