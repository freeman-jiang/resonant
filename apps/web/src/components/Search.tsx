"use client";
import { amplitude } from "@/analytics/amplitude";
import { FEED_QUERY_KEY, searchFor } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

// TODO: Replace with react hook form
export function Search() {
  const [search, setSearch] = useState("");
  const qc = useQueryClient();

  const handleSearch = async (e) => {
    e.preventDefault();

    if (search.length === 0) {
      return;
    }

    await qc.fetchQuery([FEED_QUERY_KEY], () => searchFor(search));
    amplitude.track("Search", { query: search });
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
