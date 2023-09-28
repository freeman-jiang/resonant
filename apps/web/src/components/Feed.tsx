"use client";
import { amplitude } from "@/analytics/amplitude";
import { FEED_QUERY_KEY, fetchFeed } from "@/api";
import { NEXT_PUBLIC_AMPLITUDE_API_KEY } from "@/config";
import { cn } from "@/lib/utils";
import { Link } from "@/types/api";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Entry } from "./Entry";
import { Search } from "./Search";
import { Topics } from "./Topics";
import { Skeleton } from "./ui/skeleton";

interface Props {
  links: Link[];
}

export const Feed = (props: Props) => {
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
  const { data: links } = useQuery({
    queryKey: [FEED_QUERY_KEY],
    queryFn: () => fetchFeed(),
    initialData: props.links,
  });

  return (
    <div>
      <Topics />
      <Search />
      <div className="mt-5 space-y-2">
        {links.length > 0 ? (
          links.map((link) => <Entry key={link.url} {...link} />)
        ) : (
          <LoadingFeed />
        )}
      </div>
    </div>
  );
};

interface LoadingEntryProps extends React.HTMLAttributes<HTMLDivElement> {
  index: number;
}

const LoadingEntry = ({ index, ...rest }: LoadingEntryProps) => {
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
