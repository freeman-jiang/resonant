"use client";
import { amplitude } from "@/analytics/amplitude";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { useFeed } from "@/context/FeedContext";
import axios from "axios";
import { useState } from "react";

// TODO: Replace with react hook form
export function Search() {
  const { setLinks } = useFeed();
  const [search, setSearch] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();

    if (search.length === 0) {
      return;
    }

    const linkRegex = /https?:\/\/[^\s]+/g;
    const body = linkRegex.test(search) ? { url: search } : { query: search };

    // TODO: Refactor base url into base axios instance, also consider if this link logic should be in the api
    const { data } = await axios.post(`${NEXT_PUBLIC_BASE_URL}/search`, body);
    amplitude.track("Search", { query: search });
    // Take the first 15 results
    setLinks(data.slice(0, 15));
  };

  return (
    <form
      className="mt-3 flex w-full items-center space-x-2"
      onSubmit={handleSearch}
    >
      <Input
        onChange={(e) => setSearch(e.target.value)}
        type="text"
        placeholder="Search by content or URL"
      />
      <Button type="submit">Search</Button>
    </form>
  );
}
