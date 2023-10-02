"use client";
import { amplitude } from "@/analytics/amplitude";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface Props {
  onSubmit?: (query: string) => void;
  initialQuery?: string;
}

// TODO: Replace with react hook form
export function Search({ onSubmit, initialQuery }: Props) {
  const [search, setSearch] = useState(initialQuery || "");
  const router = useRouter();

  const handleSearch = async (e) => {
    e.preventDefault();

    if (search.length === 0) {
      return;
    }

    if (onSubmit) {
      onSubmit(search);
    } else {
      amplitude.track("Search", { query: search });
      router.push(`/search?q=${search}`);
    }

    // await qc.fetchQuery({
    //   queryKey: [FEED_QUERY_KEY],
    //   queryFn: () => searchFor(search),
    // });
  };

  return (
    <form
      className="mt-3 flex w-full items-center space-x-2"
      onSubmit={handleSearch}
    >
      <Input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        type="text"
        placeholder="Search by content or URL"
      />
      <Button
        className="flex min-w-[5rem] items-center justify-center"
        type="submit"
      >
        {/* TODO: Add animation to make less jarring */}
        {"Search"}
      </Button>
    </form>
  );
}
