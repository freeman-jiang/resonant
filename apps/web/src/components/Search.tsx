"use client";
import { amplitude } from "@/analytics/amplitude";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NEXT_PUBLIC_AMPLITUDE_API_KEY } from "@/config";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
        strokeWidth="4"
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
  useEffect(() => {
    if (!NEXT_PUBLIC_AMPLITUDE_API_KEY) {
      console.log("NEXT_PUBLIC_AMPLITUDE_API_KEY is not set");
      return;
    }
    amplitude.init(NEXT_PUBLIC_AMPLITUDE_API_KEY || "", {
      defaultTracking: {
        formInteractions: false,
        pageViews: true,
        sessions: true,
      },
    });
  }, []);

  const [search, setSearch] = useState("");
  const qc = useQueryClient();
  const router = useRouter();

  const handleSearch = async (e) => {
    e.preventDefault();

    if (search.length === 0) {
      return;
    }

    router.push(`/search?q=${search}`);

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
