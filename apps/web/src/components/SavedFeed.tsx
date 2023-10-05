"use client";
import { getSavedPages } from "@/api";
import { useSupabase } from "@/supabase/client";
import { Page } from "@/types/api";
import { useEffect, useState } from "react";
import { Feed } from "./Feed";

interface Props {
  feed: Page[];
}

export const SavedFeed = ({ feed: serverFeed }: Props) => {
  const {
    session: { user },
  } = useSupabase();
  const [feed, setFeed] = useState<Page[]>(serverFeed);

  useEffect(() => {
    const fetchFeed = async () => {
      const pages = await getSavedPages(user.id);
      setFeed(pages);
    };
    fetchFeed();
  }, [user.id]);

  return <Feed feed={feed} />;
};
