"use client";
import { cn } from "@/lib/utils";
import { User } from "@supabase/auth-helpers-nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "../ui/button";

interface Props {
  user: User;
}

export const RightButton = ({ user }: Props) => {
  const path = usePathname();
  if (!!user) {
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
