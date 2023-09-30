"use client";
import { useFeed } from "@/api/hooks";
import { cn } from "@/lib/utils";
import { Entry } from "./Entry";
import { Skeleton } from "./ui/skeleton";

export const Feed = () => {
  const { data } = useFeed();

  return (
    <div className="mt-5 space-y-2">
      {data.map((page) => (
        <Entry {...page} key={page.url} />
      ))}
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
    skeletons.push(<LoadingEntry key={i} index={i} />);
  }
  return skeletons;
};

export const LoadingFeed = () => {
  return <div className="mt-4 w-full space-y-4">{renderSkeletons(20)}</div>;
};
