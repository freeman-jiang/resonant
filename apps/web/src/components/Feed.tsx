"use client";
import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { FeedContext } from "@/context/FeedContext";
import { cn } from "@/lib/utils";
import { Link } from "@/types/api";
import { useEffect, useState } from "react";
import { Entry } from "./Entry";
import { Search } from "./Search";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";

// TODO: Consider using SSR by making this a server component
async function getData() {
  const response = await fetch(`${NEXT_PUBLIC_BASE_URL}/feed`, {
    cache: "no-store",
    next: {
      tags: ["pages"],
      // revalidate: 30, // Clear cache every 30 seconds (there is a bug with this that causes the entire page to hang instead of just the Suspense component)
    },
  });
  return response.json() as Promise<Link[]>;
}

export const Feed = () => {
  // TODO: Replace with tanstack-query
  const [links, setLinks] = useState<Link[]>([]);

  useEffect(() => {
    getData().then((data) => {
      setLinks(data);
    });
  }, []);

  return (
    <FeedContext.Provider value={{ setLinks }}>
      <div className="mt-3 flex flex-row gap-2 pb-2">
        <Badge className="cursor-pointer text-sm">All</Badge>
        <Badge className="cursor-pointer text-sm" variant="outline">
          Software
        </Badge>
        <Badge className="cursor-pointer text-sm" variant="outline">
          Climate
        </Badge>
        <Badge className="cursor-pointer text-sm" variant="outline">
          Philosophy
        </Badge>
      </div>
      <Search />
      <div className="mt-5 space-y-2">
        {links.length > 0 ? (
          links.map((link) => <Entry key={link.url} {...link} />)
        ) : (
          <LoadingFeed />
        )}
      </div>
    </FeedContext.Provider>
  );
};

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  index: number;
}

const LoadingEntry = ({ index, ...rest }: Props) => {
  const isLarger = index % 3 === 0;

  return (
    <>
      <Skeleton
        className={cn("bg-slate-200", {
          "h-12": isLarger,
          "h-8": !isLarger,
        })}
      />
      <Skeleton className="mt-2 h-6" />
    </>
  );
};

const renderSkeletons = (count: number) => {
  const skeletons = [];

  for (let i = 0; i < count; i++) {
    skeletons.push(<LoadingEntry index={i} />);
  }
  return skeletons;
};

export const LoadingFeed = () => {
  return <div className="mt-4 w-full space-y-4">{renderSkeletons(20)}</div>;
};
