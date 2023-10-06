"use client";
import { usePage } from "@/api/hooks";
import { RelatedFeed } from "@/components/RelatedFeed";
import { ShareButton } from "@/components/ShareButton";
import { Session } from "@supabase/supabase-js";
import NextLink from "next/link";
import { AddPage } from "./AddPage";
import { PageBox } from "./PageBox";
import { SaveButton } from "./SaveButton";
import { Button } from "./ui/button";

interface Props {
  url: string;
  session: Session;
}

export const PageLayout = ({ url, session }: Props) => {
  const { data, error } = usePage(url, session);

  if (!data || error) {
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

  if (data.type == "should_add") {
    return <AddPage url={url} />;
  }

  const { page } = data;

  return (
    <div className="mt-5">
      <PageBox data={page} />
      <div className="mt-4 flex gap-3">
        <ShareButton url={page.url} />
        <SaveButton page={page} />
      </div>

      {/* <SearchBoundary query={url}> */}
      <RelatedFeed url={url} />
      {/* </SearchBoundary> */}
    </div>
  );
};
