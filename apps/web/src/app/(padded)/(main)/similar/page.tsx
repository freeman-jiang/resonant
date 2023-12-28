import { GlobalFeed } from "@/components/GlobalFeed";
import { InboxFeed } from "@/components/feeds/InboxFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Inbox() {
  const { session } = await getSupabaseServer();
  const user = session?.user;

  if (!user) {
    return <GlobalFeed />;
  }

  return <InboxFeed userId={user.id} />;
}
