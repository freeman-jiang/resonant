import { cn } from "@/lib/utils";
import { Page } from "@/types/api";
import { Entry } from "./Entry";
import { Skeleton } from "./ui/skeleton";

interface Props {
  feed?: Page[];
}

export const Feed = ({ feed }: Props) => {
  if (!feed) {
    return (
      <div className="mt-5">
        <LoadingFeed />
      </div>
    );
  }

  return (
    <div className="mt-5 space-y-2">
      {feed.slice(0, 50).map((page) => (
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
