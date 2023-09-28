import { Link } from "@/types/api";
import { FeedbackButton } from "./FeedbackButton";

export const extractDomain = (url: string) => {
  const domain = url.split("/")[2];
  return domain.split(":")[0];
};

// TODO: Consider moving this to backend
const punctuationSet = new Set([".", ",", "!", "?", ";", ":", "-"]);
const MAX_EXCERPT_LENGTH = 200;
const formatExercept = (excerpt: string) => {
  // Limit to 190 characters but make sure we don't cut off a word
  if (excerpt.length < MAX_EXCERPT_LENGTH) {
    return excerpt;
  }

  const lastSpaceIndex = excerpt.lastIndexOf(" ", MAX_EXCERPT_LENGTH);
  // If no space found, just truncate at the maxLength
  if (lastSpaceIndex === -1) {
    excerpt = excerpt.substring(0, MAX_EXCERPT_LENGTH);
  } else {
    excerpt = excerpt.substring(0, lastSpaceIndex);
  }

  if (punctuationSet.has(excerpt.at(-1))) {
    // Remove trailing punctuation
    excerpt = excerpt.substring(0, excerpt.length - 1);
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
        <p className="mt-2 font-mono text-sm text-slate-500">
          {formatExercept(link.excerpt)}
        </p>
      </div>
    </div>
  );
};
