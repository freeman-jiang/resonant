import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { Link } from "@/types/api";
import axios from "axios";

// TODO: Consider using SSR by making this a server component
export const FEED_QUERY_KEY = "feed";

export async function fetchFeed() {
  const response = await fetch(`${NEXT_PUBLIC_BASE_URL}/random-feed`, {
    next: {
      revalidate: 1800, // Refresh every half hour
    },
  });
  return response.json() as Promise<Link[]>;
}

export const searchFor = async (query: string) => {
  const linkRegex = /https?:\/\/[^\s]+/g;
  const body = linkRegex.test(query) ? { url: query } : { query: query };

  const { data } = await axios.post(`${NEXT_PUBLIC_BASE_URL}/search`, body);
  return data as Link[];
};
