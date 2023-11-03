import { GlobalFeed } from "@/components/GlobalFeed";
import { InboxFeed } from "@/components/feeds/InboxFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Home() {
  const { session } = await getSupabaseServer();
  const user = session?.user;

  if (!user) {
    return <GlobalFeed />;
  }

  return (
    <InboxFeed userId={user.id} />
    // <UserFeedBoundary userId={user.id}>
    // <UserFeed userId={user?.id} />
    // </UserFeedBoundary>
  );
}
