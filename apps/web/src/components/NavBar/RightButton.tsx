"use client";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "../ui/button";

export const RightButton = () => {
  const path = usePathname();

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
