import { getUser } from "@/api";
import "@/app/globals.css";
import { Search } from "@/components/Search";
import { Topics } from "@/components/Topics";
import { Toaster } from "@/components/ui/toaster";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Providers } from "../providers";

// export const dynamic = "force-dynamic";

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (user) {
    // TODO: Maybe call supabase directly instead
    const u = await getUser(user.id);
    if (!u) {
      redirect("/new");
    }
  }

  return (
    <Providers>
      <div className="mx-auto p-8 lg:max-w-2xl">
        <Link href="/" className="text-2xl font-bold">
          Superstack
        </Link>
        <Topics />
        <Search />
        {children}
      </div>
      <Toaster />
    </Providers>
  );
}
