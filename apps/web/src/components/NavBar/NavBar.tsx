import Link from "next/link";
import { UserNav } from "./UserNav";

export async function NavBar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  return (
    <div className="border-b">
      <div className="flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-xl font-bold">
          Superstack
        </Link>
        <UserNav />
      </div>
    </div>
  );
}
