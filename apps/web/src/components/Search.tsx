"use client";
import { amplitude } from "@/analytics/amplitude";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "next/navigation";
import { SubmitHandler, useForm } from "react-hook-form";

interface Inputs {
  search: string;
}

export function Search() {
  const router = useRouter();
  const { register, handleSubmit } = useForm<Inputs>();

  const onSubmit: SubmitHandler<Inputs> = async ({ search }) => {
    if (search.length === 0) {
      return;
    }
    amplitude.track("Search", { query: search });

    const linkRegex = /https?:\/\/[^\s]+/g;
    if (search.match(linkRegex)) {
      router.push(`/c?url=${search}`);
      return;
    }

    router.push(`/search?q=${search}`);
  };

  return (
    <form
      className="mb-5 mt-3 flex w-full items-center space-x-2"
      onSubmit={handleSubmit(onSubmit)}
    >
      <Input
        {...register("search")}
        type="text"
        placeholder="Search by content or URL"
        className="md:text-base"
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
