"use client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NEXT_PUBLIC_BASE_URL } from "@/config";
import { useFeed } from "@/context/FeedContext";
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

    const response = await fetch(`${NEXT_PUBLIC_BASE_URL}/search/${search}`);
    const results = await response.json();
    setLinks(results);
  };

  return (
    <form
      className="mt-3 flex w-full items-center space-x-2"
      onSubmit={handleSearch}
    >
      <Input
        onChange={(e) => setSearch(e.target.value)}
        type="text"
        placeholder="Paste a URL to find similar content"
      />
      <Button type="submit">Search</Button>
    </form>
  );
}
