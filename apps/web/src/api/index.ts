import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { Page } from "@/types/api";
import { Session } from "@supabase/supabase-js";
import baseAxios from "axios";

const axios = baseAxios.create({
  baseURL: NEXT_PUBLIC_BASE_URL,
});

export interface Sender {
  id: string;
  first_name: string;
  last_name: string;
  profile_picture_url: string;
  sent_on: string; // python datetime.datetime
}

export interface FeedResponse {
  random_feed: Page[];
  messages: Page[];
}

export async function fetchSocialFeed() {
  const response = await axios.get<FeedResponse>(`/feed`);
  return response.data;
}

export async function fetchFeed() {
  const response = await fetch(`${NEXT_PUBLIC_BASE_URL}/random-feed`, {
    next: {
      revalidate: 1800, // Refresh every half hour
    },
  });
  return response.json() as Promise<Page[]>;
}

export const searchFor = async (query: string) => {
  const linkRegex = /https?:\/\/[^\s]+/g;
  const body = linkRegex.test(query) ? { url: query } : { query: query };

  const { data } = await axios.post(`/search`, body);
  return data as Page[];
};

export interface Crawl {
  title: string;
  excerpt: string;
  url: string;
  type: "crawl";
}
interface AlreadyAdded {
  type: "already_added";
  url: string;
}

export type CrawlInteractiveResponse = Crawl | AlreadyAdded;

export const crawlUrl = async (url: string) => {
  const { data } = await axios.post<CrawlInteractiveResponse>(`/crawl`, {
    url,
  });
  return data;
};

interface ExistingPageResponse {
  page: Page;
  has_broadcasted: boolean;
  type: "page";
}

interface ShouldAdd {
  type: "should_add";
  url: string;
}

type FindPageResponse = ShouldAdd | ExistingPageResponse;

export const findPage = async (url: string, session?: Session) => {
  const { data } = await axios.post<FindPageResponse>(`/page`, {
    url,
    userId: session?.user.id,
  });

  return data;
};

export interface CreateUserRequest {
  email: string;
  id: string;
  firstName: string;
  lastName: string;
  profileUrl?: string;
}
export const createUser = async (user: CreateUserRequest) => {
  const { data } = await axios.post(`/create_user`, user);
  return data;
};

// TODO: fill in object with user type
type GetUserResponse = null | {};

export const getUser = async (uuid: string): Promise<GetUserResponse> => {
  const { data } = await axios.get(`/user/${uuid}`);
  return data; // replace with User;
};

export const savePage = async (userId: string, pageId: number) => {
  const { data } = await axios.get(`/save/${userId}/${pageId}`);
  return data;
};

export const unsavePage = async (userId: string, pageId: number) => {
  const { data } = await axios.delete(`/unsave/${userId}/${pageId}`);
  return data;
};

export const getSavedPages = async (userId: string) => {
  const { data } = await axios.get<Page[]>(`/saved/${userId}`);
  return data;
};

export const sharePage = async (userId: string, pageId: number) => {
  const { data } = await axios.post(`/share/${userId}/${pageId}`);
  return data;
};

export const unsharePage = async (userId: string, pageId: number) => {
  const { data } = await axios.post(`/unshare/${userId}/${pageId}`);
  return data;
};

export const addPage = async (userid: string, url: string) => {
  const { data } = await axios.post<Page>(`/add_page`, { userid, url });
  return data;
};
