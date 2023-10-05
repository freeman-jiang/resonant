import { getUser } from "@/api";
import "@/app/globals.css";
import { Search } from "@/components/Search";
import { Topics } from "@/components/Topics";
import { Toaster } from "@/components/ui/toaster";
import { SupabaseProvider } from "@/supabase/client";
import { getSupabaseServer } from "@/supabase/server";
import { redirect } from "next/navigation";
import { Providers } from "../providers";

// export const dynamic = "force-dynamic";

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { session } = await getSupabaseServer();
  const user = session?.user;

  if (user) {
    // TODO: Maybe call supabase directly instead
    const u = await getUser(user.id);
    if (!u) {
      redirect("/new");
    }
  }

  return (
    <SupabaseProvider session={session}>
      <Providers>
        <div className="mx-auto px-8 py-4 md:max-w-2xl">
          <Topics />
          <Search />
          {children}
        </div>
        <Toaster />
      </Providers>
    </SupabaseProvider>
  );
}
