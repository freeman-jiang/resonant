import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const extractDomain = (url: string) => {
  const domain = url.split("/")[2];
  return domain.split(":")[0];
};

// TODO: Consider moving this to backend
const punctuationSet = new Set([".", ",", "!", "?", ";", ":", "-"]);
const DEFAULT_MAX_EXCERPT_LENGTH = 200;
export const formatExercept = (
  excerpt: string,
  maxLength = DEFAULT_MAX_EXCERPT_LENGTH,
) => {
  // Limit to 190 characters but make sure we don't cut off a word
  if (excerpt.length < maxLength) {
    return excerpt;
  }

  const lastSpaceIndex = excerpt.lastIndexOf(" ", maxLength);
  // If no space found, just truncate at the maxLength
  if (lastSpaceIndex === -1) {
    excerpt = excerpt.substring(0, maxLength);
  } else {
    excerpt = excerpt.substring(0, lastSpaceIndex);
  }

  if (punctuationSet.has(excerpt.at(-1))) {
    // Remove trailing punctuation
    excerpt = excerpt.substring(0, excerpt.length - 1);
  }
  return `${excerpt}...`;
};
