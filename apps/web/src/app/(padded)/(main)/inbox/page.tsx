import { InboxFeed } from "@/components/feeds/InboxFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Inbox() {
  const {
    session: { user },
  } = await getSupabaseServer({ protected: true });

  return <InboxFeed userId={user.id} />;
}
