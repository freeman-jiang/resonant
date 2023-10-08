"use client";
import { useCrawl } from "@/api/hooks";
import Link from "next/link";
import { LoadingFeed } from "./Feed";
import { PageBox } from "./PageBox";
import { RelatedFeed } from "./RelatedFeed";
import { StoreButton } from "./StoreButton";
import { Button } from "./ui/button";
import { Skeleton } from "./ui/skeleton";

interface Props {
  url: string;
}

export const AddPage = ({ url }: Props) => {
  const { data, error } = useCrawl(url);

  if (error) {
    return (
      <div>
        <div className="font-semibold">Could not crawl </div>
        <div className="break-all font-mono">{url}</div>
        <div>
          <Link href="/" className="mt-2">
            <Button variant="link" className="p-0">
              Back home
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <Skeleton className="h-48 w-full" />
        <LoadingFeed />
      </div>
    );
  }

  if (data.type == "already_added") {
    return <div>already added</div>;
  }

  return (
    <div>
      <PageBox data={data} />
      <div className="mt-4">
        <StoreButton url={data.url} />
      </div>
      <RelatedFeed url={data.url} />
    </div>
  );
};
