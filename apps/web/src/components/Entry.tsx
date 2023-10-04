import { extractDomain, formatExercept } from "@/lib/utils";
import { Page } from "@/types/api";
import NextLink from "next/link";
import { FeedbackButton } from "./FeedbackButton";

export const Entry = (link: Page) => {
  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="flex flex-row items-center justify-between">
          <NextLink href={`/c?url=${link.url}`} className="cursor-pointer">
            <h2 className="text-xl font-semibold tracking-tight text-slate-900">
              {link.title || link.url}
            </h2>
            <p className="text-sm font-light text-slate-700">
              {extractDomain(link.url)}
            </p>
          </NextLink>
          <FeedbackButton page={link} className="ml-8 lg:ml-20" />
        </div>
        <p className="mt-2 font-mono text-sm text-slate-500">
          {formatExercept(link.excerpt)}
        </p>
      </div>
    </div>
  );
};
