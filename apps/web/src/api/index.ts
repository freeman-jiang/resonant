import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { Link } from "@/types/api";
import axios from "axios";

// TODO: Consider using SSR by making this a server component
export async function fetchFeed() {
  const response = await fetch(`${NEXT_PUBLIC_BASE_URL}/feed`, {
    cache: "no-store",
    next: {
      tags: ["pages"],
      // revalidate: 30, // Clear cache every 30 seconds (there is a bug with this that causes the entire page to hang instead of just the Suspense component)
    },
  });
  return response.json() as Promise<Link[]>;
}

export const searchFor = async (topic: string) => {
  const { data } = await axios.post(`${NEXT_PUBLIC_BASE_URL}/search`, {
    query: topic,
  });
  return data as Link[];
};
