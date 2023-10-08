"use client";
import { cn } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "../ui/button";

export const RightButton = () => {
  const { session } = useSupabase();

  const path = usePathname();
  if (!!session) {
    return null;
  }

  if (path === "/login") {
    return (
      <Link className={cn(buttonVariants({ variant: "link" }))} href="/">
        Feed
      </Link>
    );
  }

  return (
    <Link className={cn(buttonVariants({ variant: "link" }))} href="/login">
      Login
    </Link>
  );
};
