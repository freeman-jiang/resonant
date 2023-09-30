import { findPage } from "@/api";
import { LoadingFeed } from "@/components/Feed";
import { RelatedFeed } from "@/components/RelatedFeed";
import { extractDomain, formatExercept } from "@/lib/utils";
import NextLink from "next/link";
import { Suspense } from "react";

interface RouteProps {
  searchParams: {
    url: string;
  };
}

export default async function Page(params: RouteProps) {
  const { url } = params.searchParams;
  const page = await findPage(url);

  return (
    <div className="mt-5">
      <NextLink href={page.url} target="_blank" className="cursor-pointer">
        <div className="border border-slate-200 px-3 py-3">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
            {page.title || page.url}
          </h2>
          <p className="text-sm font-light text-slate-700">
            {extractDomain(page.url)}
          </p>
          <p className="mt-2 font-mono text-sm text-slate-500">
            {formatExercept(page.excerpt)}
          </p>
        </div>
      </NextLink>

      <h2 className="mt-5 text-2xl font-semibold text-slate-900">Related</h2>
      <Suspense fallback={<LoadingFeed />}>
        <RelatedFeed url={url} />
      </Suspense>
    </div>
  );
}
