"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "../ui/button";

export function NavBar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const path = usePathname();
  const isLogin = path === "/login";

  return (
    <div className="border-b">
      <div className="flex h-16 items-center justify-between px-4">
        <h1 className="text-xl font-bold">Superstack</h1>
        <Link href={isLogin ? "/" : "/login"}>
          <Button variant="outline">{isLogin ? "Home" : "Login"}</Button>
        </Link>
      </div>
    </div>
  );
}
