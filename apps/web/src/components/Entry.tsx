import { Link } from "@/types/api";
import { FeedbackButton } from "./FeedbackButton";

export const extractDomain = (url: string) => {
  const domain = url.split("/")[2];
  return domain.split(":")[0];
};

const formatExercept = (excerpt: string) => {
  // Limit to 230 characters
  excerpt = excerpt.slice(0, 230);

  if (excerpt.at(-1) === ".") {
    return `${excerpt}..`;
  }
  return `${excerpt}...`;
};

export const Entry = (link: Link) => {
  return (
    <div>
      <div className="border-b border-slate-400 pb-2">
        <div className="flex flex-row items-center justify-between">
          <a href={link.url} className="cursor-pointer" target="_blank">
            <h2 className="scroll-m-20 text-xl font-semibold tracking-tight text-slate-900">
              {link.title}
            </h2>
            <p className="text-sm font-light text-slate-700">
              {extractDomain(link.url)}
            </p>
          </a>
          <FeedbackButton link={link} className="ml-8 lg:ml-20" />
        </div>
        <p className="mt-2 font-mono text-xs text-slate-500">
          {formatExercept(link.excerpt)}
        </p>
      </div>
    </div>
  );
};
