import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { cn } from "@/lib/utils";
import { Link } from "@/types/api";
import { Entry } from "./Entry";
import { Skeleton } from "./ui/skeleton";

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

export const Feed = async () => {
  const links = await getData();

  return (
    <div className="mt-4 space-y-2">
      {links.map((link) => (
        <Entry key={link.url} {...link} />
      ))}
    </div>
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
