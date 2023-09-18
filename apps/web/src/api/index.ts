import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { Link } from "@/types/api";
import axios from "axios";

// TODO: Consider using SSR by making this a server component
export async function fetchFeed() {
  const response = await fetch(`${NEXT_PUBLIC_BASE_URL}/random-feed`, {
    next: {
      revalidate: 1800, // Refresh every half hour
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
