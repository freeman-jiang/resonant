import { GlobalFeed } from "@/components/GlobalFeed";
import { ForYouFeed } from "@/components/feeds/ForYouFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Home() {
  const { session } = await getSupabaseServer();
  const user = session?.user;

  if (!user) {
    return <GlobalFeed />;
  }

  return <ForYouFeed userId={user.id} />;
}
