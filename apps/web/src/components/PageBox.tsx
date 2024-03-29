import { trackClickOutboundLink } from "@/analytics/mixpanel";
import { Crawl, Page } from "@/api";
import { extractDomain, formatExcerpt } from "@/lib/utils";
import { ExternalLink } from "lucide-react";
import Link from "next/link";

interface Props {
  data: Page | Crawl;
}

export const PageBox = ({ data }: Props) => {
  return (
    <Link
      onClick={() => trackClickOutboundLink(data.url)}
      href={data.url}
      target="_blank"
      className="cursor-pointer"
    >
      <div className="border border-slate-200 px-3 py-3">
        <div className="flex flex-row justify-between space-x-4">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
            {data.title || data.url}
          </h2>
          <ExternalLink className="mt-2 block h-5 w-5 flex-shrink-0" />
        </div>
        <p className="text-sm font-light text-slate-700">
          {extractDomain(data.url)}
        </p>
        <p className="mt-2 break-all font-mono text-sm text-slate-500">
          {formatExcerpt(data.excerpt, 500)}
        </p>
      </div>
    </Link>
  );
};
