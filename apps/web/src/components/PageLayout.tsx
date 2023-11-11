"use client";
import { usePage } from "@/api/hooks";
import { Session } from "@supabase/supabase-js";
import NextLink from "next/link";
import { AddPage } from "./AddPage";
import { ExistingPage } from "./ExistingPage";
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

  return <ExistingPage data={data} />;
};
