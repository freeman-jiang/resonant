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
export const formatExcerpt = (
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

export function getRelativeTime(pythonDatetimeString: string): string {
  // Parse the Python datetime string into a JavaScript Date object
  const parsedDate = new Date(pythonDatetimeString);

  // Get the current date
  const currentDate = new Date();

  // Calculate the time difference in seconds
  const differenceInSeconds =
    (currentDate.getTime() - parsedDate.getTime()) / 1000;

  // Define the time intervals
  const minute = 60;
  const hour = minute * 60;
  const day = hour * 24;
  const month = day * 30;
  const year = day * 365;

  if (differenceInSeconds < minute) {
    return `just now`;
  } else if (differenceInSeconds < hour) {
    if (Math.floor(differenceInSeconds / minute) === 1) {
      return `1 minute ago`;
    } else {
      return `${Math.floor(differenceInSeconds / minute)} minutes ago`;
    }
  } else if (differenceInSeconds < day) {
    if (Math.floor(differenceInSeconds / hour) === 1) {
      return `1 hour ago`;
    } else {
      return `${Math.floor(differenceInSeconds / hour)} hours ago`;
    }
  } else if (differenceInSeconds < month) {
    if (Math.floor(differenceInSeconds / day) === 1) {
      return `1 day ago`;
    } else {
      return `${Math.floor(differenceInSeconds / day)} days ago`;
    }
  } else if (differenceInSeconds < year) {
    if (Math.floor(differenceInSeconds / month) === 1) {
      return `1 month ago`;
    } else {
      return `${Math.floor(differenceInSeconds / month)} months ago`;
    }
  } else {
    if (Math.floor(differenceInSeconds / year) === 1) {
      return `1 year ago`;
    } else {
      return `${Math.floor(differenceInSeconds / year)} years ago`;
    }
  }
}

export const formatFullName = (firstName: string, lastName: string) => {
  return `${firstName} ${lastName}`;
};
