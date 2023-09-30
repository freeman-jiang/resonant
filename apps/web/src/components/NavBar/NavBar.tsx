import Link from "next/link";
import { Button } from "../ui/button";

export function NavBar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  return (
    <div className="border-b">
      <div className="flex h-16 items-center justify-between px-4">
        <h1 className="text-xl font-bold">Superstack</h1>
        <Link href="/login">
          <Button variant="outline">Login</Button>
        </Link>
      </div>
    </div>
  );
}
