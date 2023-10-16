"use client";
import { usePage } from "@/api/hooks";
import { RelatedFeed } from "@/components/RelatedFeed";
import { SendButton } from "@/components/SendButton";
import { Session } from "@supabase/supabase-js";
import NextLink from "next/link";
import { AddPage } from "./AddPage";
import { BroadcastButton } from "./BroadcastButton";
import { LikeButton } from "./LikeButton";
import { LinkedBy } from "./LinkedBy";
import { PageBox } from "./PageBox";
import { PageComments } from "./PageComments";
import { Senders } from "./Senders";
import { Button } from "./ui/button";

interface Props {
  url: string;
  session: Session;
}

export const PageLayout = ({ url, session }: Props) => {
  const { data, error } = usePage(url, session);

  if (!data || error) {
    return (
      <div>
        Could not crawl <span className="font-mono">{url}</span>
        <div>
          <NextLink href="/">
            <Button variant="link" className="p-0">
              Back home
            </Button>
          </NextLink>
        </div>
      </div>
    );
  }

  if (data.type == "should_add") {
    return <AddPage url={url} />;
  }

  const { page } = data;

  return (
    <div>
      <PageBox data={page} />
      <div>
        <Senders senders={page.senders} />
        <LinkedBy page={page} />
      </div>
      <div className="mt-4 flex gap-3">
        <SendButton url={url} />
        <BroadcastButton url={url} />
        <LikeButton page={page} />
      </div>

      <div className="mt-4">
        <h2 className="text-xl font-semibold text-slate-900">
          Discussion <span>({data.num_comments})</span>
        </h2>
        <PageComments data={data} />
      </div>

      {/* <SearchBoundary query={url}> */}
      <RelatedFeed url={url} />
      {/* </SearchBoundary> */}
    </div>
  );
};
