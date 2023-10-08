import { UserBoundary } from "@/api/hooks";
import { getSupabaseServer } from "@/supabase/server";
import Link from "next/link";
import { RightButton } from "./RightButton";
import { UserNav } from "./UserNav";

export const dynamic = "force-dynamic";

export async function NavBar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const { session } = await getSupabaseServer();
  return (
    <div className="border-b">
      <div className="flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-xl font-semibold">
          Resonant
        </Link>

        <div className="flex items-center gap-2">
          <UserBoundary session={session}>
            <UserNav />
            <RightButton />
          </UserBoundary>
        </div>
      </div>
    </div>
  );
}
