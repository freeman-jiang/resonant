import { trackClickLinkedBy } from "@/analytics/mixpanel";
import { Page } from "@/api";
import { extractDomain } from "@/lib/utils";
import Link from "next/link";
import { Fragment } from "react";

interface Props {
  page: Page;
}

export const LinkedBy = ({ page }: Props) => {
  if (page.linked_by.length === 0) {
    return null;
  }

  return (
    <div className="mt-2 text-xs text-slate-500">
      <span className="">Linked by: </span>
      {page.linked_by.map((parentUrl, index) => (
        <Fragment key={parentUrl}>
          <Link
            href={parentUrl}
            target="_blank"
            className="text-emerald-600"
            onClick={() => trackClickLinkedBy(page.url, parentUrl)}
          >
            {extractDomain(parentUrl)}
          </Link>
          {index !== page.linked_by.length - 1 && ", "}
        </Fragment>
      ))}
    </div>
  );
};
