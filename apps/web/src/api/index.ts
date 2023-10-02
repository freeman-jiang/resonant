import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { Link } from "@/types/api";
import axios from "axios";

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

export const findPage = async (url: string) => {
  const { data } = await axios.post(`${NEXT_PUBLIC_BASE_URL}/page`, { url });
  return data as Link;
};

interface CreateUserRequest {
  email: string;
  id: string;
  firstName: string;
  lastName: string;
}
export const createUser = async (user: CreateUserRequest) => {
  const { data } = await axios.post(
    `${NEXT_PUBLIC_BASE_URL}/create_user`,
    user,
  );
  return data;
};

export const getUser = async (uuid: string) => {
  const { data } = await axios.get(`${NEXT_PUBLIC_BASE_URL}/user/${uuid}`);
  return data;
};
