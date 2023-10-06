"use client";
import { useCrawl } from "@/api/hooks";
import { LoadingFeed } from "./Feed";
import { PageBox } from "./PageBox";
import { RelatedFeed } from "./RelatedFeed";
import { StoreButton } from "./StoreButton";
import { Skeleton } from "./ui/skeleton";

interface Props {
  url: string;
}

export const AddPage = ({ url }: Props) => {
  const { data } = useCrawl(url);

  if (!data) {
    return (
      <div className="mt-5">
        <Skeleton className="h-48 w-full" />
        <LoadingFeed />
      </div>
    );
  }

  return (
    <div className="mt-5">
      <PageBox data={data} />
      <div className="mt-3">
        <StoreButton url={data.url} />
      </div>
      <RelatedFeed url={data.url} />
    </div>
  );
};
