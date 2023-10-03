import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import Link from "next/link";
import { UserNav } from "./UserNav";

export const dynamic = "force-dynamic";

const getUser = async () => {
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return user;
};

export async function NavBar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const user = await getUser();
  return (
    <div className="border-b">
      <div className="flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-xl font-bold">
          Resonant
        </Link>
        <UserNav user={user} />
      </div>
    </div>
  );
}
