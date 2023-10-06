"use client";
import { usePage } from "@/api/hooks";
import { RelatedFeed } from "@/components/RelatedFeed";
import { ShareButton } from "@/components/ShareButton";
import { Session } from "@supabase/supabase-js";
import NextLink from "next/link";
import { PageBox } from "./PageBox";
import { SaveButton } from "./SaveButton";
import { Button } from "./ui/button";

interface Props {
  url: string;
  session: Session;
}

export const PageLayout = ({ url, session }: Props) => {
  const { data, error } = usePage(url, session);

  if (!data || error || data.type !== "page") {
    return (
      <div className="mt-5">
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

  const { page } = data;

  return (
    <div className="mt-5">
      <PageBox data={page} />
      <div className="mt-4 flex gap-3">
        <ShareButton url={page.url} />
        <SaveButton page={page} />
      </div>
      <h2 className="mt-5 text-2xl font-semibold text-slate-900">Related</h2>

      {/* <SearchBoundary query={url}> */}
      <RelatedFeed url={url} />
      {/* </SearchBoundary> */}
    </div>
  );
};
