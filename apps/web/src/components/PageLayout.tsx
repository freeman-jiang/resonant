"use client";
import { usePage } from "@/api/hooks";
import { RelatedFeed } from "@/components/RelatedFeed";
import { SaveButton } from "@/components/SaveButton";
import { ShareButton } from "@/components/ShareButton";
import { extractDomain, formatExercept } from "@/lib/utils";
import { Session } from "@supabase/supabase-js";
import { ExternalLink } from "lucide-react";
import NextLink from "next/link";

interface Props {
  url: string;
  session: Session;
}

export const PageLayout = ({ url, session }: Props) => {
  const {
    data: { page },
  } = usePage(url, session);

  return (
    <div className="mt-5">
      <NextLink href={page.url} target="_blank" className="cursor-pointer">
        <div className="border border-slate-200 px-3 py-3">
          <div className="flex flex-row justify-between space-x-4">
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
              {page.title || page.url}
            </h2>
            <ExternalLink className="mt-2 block h-5 w-5 flex-shrink-0" />
          </div>
          <p className="text-sm font-light text-slate-700">
            {extractDomain(page.url)}
          </p>
          <p className="mt-2 font-mono text-sm text-slate-500">
            {formatExercept(page.excerpt, 500)}
          </p>
        </div>
      </NextLink>

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