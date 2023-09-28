"use client";
import { amplitude } from "@/analytics/amplitude";
import { searchFor } from "@/api";
import { FEED_QUERY_KEY } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

const Spinner = () => {
  return (
    <svg
      className="h-5 w-5 animate-spin text-white"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
};

// TODO: Replace with react hook form
export function Search() {
  const [search, setSearch] = useState("");
  const qc = useQueryClient();
  const [isLoading, setIsLoading] = useState(false);
  console.log(isLoading);

  const handleSearch = async (e) => {
    e.preventDefault();

    if (search.length === 0) {
      return;
    }

    setIsLoading(true);
    await qc.fetchQuery([FEED_QUERY_KEY], () => searchFor(search));
    setIsLoading(false);
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
      <Button
        className="flex min-w-[5rem] items-center justify-center"
        type="submit"
      >
        {isLoading ? <Spinner /> : "Search"}
      </Button>
    </form>
  );
}
