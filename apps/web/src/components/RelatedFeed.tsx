import { searchFor } from "@/api";
import { Entry } from "./Entry";

interface Props {
  url: string;
}

export const RelatedFeed = async ({ url }: Props) => {
  const related = await searchFor(url);

  return (
    <div className="mt-5 space-y-2">
      {related.map((page) => (
        <Entry key={page.url} {...page} />
      ))}
    </div>
  );
};
