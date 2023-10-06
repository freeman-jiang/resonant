"use client";
import { useCrawl } from "@/api/hooks";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
  const router = useRouter();

  if (error) {
    return (
      <div className="mt-5">
        Could not crawl <span className="font-mono">{url}</span>
        <div>
          <Link href="/">
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
      <div className="mt-5">
        <Skeleton className="h-48 w-full" />
        <LoadingFeed />
      </div>
    );
  }

  if (data.type == "already_added") {
    router.replace(`/c?url=${url}`);
    return;
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
