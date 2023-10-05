"use client";
import { useCrawl } from "@/api/hooks";
import { extractDomain, formatExercept } from "@/lib/utils";
import { ExternalLink } from "lucide-react";
import NextLink from "next/link";
import { Feed } from "./Feed";

interface Props {
  url: string;
}

export const AddPage = ({ url }: Props) => {
  const { data } = useCrawl(url);

  const page = data;

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
            {formatExercept(page.content, 500)}
          </p>
        </div>
      </NextLink>
      <Feed feed={page.similar} />
    </div>
  );
};
