import {UserResponse} from "@/api";

export interface Page {
  title: string;
  url: string;
  id: number;
  date: string;
  excerpt: string;
  senders: UserResponse[]
}
