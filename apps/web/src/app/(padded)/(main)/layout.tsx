import { getUser } from "@/api";
import "@/app/globals.css";
import { Search } from "@/components/Search";
import { Topics } from "@/components/Topics";
import { SupabaseProvider } from "@/supabase/client";
import { getSupabaseServer } from "@/supabase/server";
import { redirect } from "next/navigation";

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
      redirect("/onboarding");
    }
  }

  return (
    <SupabaseProvider session={session}>
      <Topics />
      <Search />
      {children}
    </SupabaseProvider>
  );
}
