import { UserFeedBoundary } from "@/api/hooks";
import { UserFeed } from "@/components/UserFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Home() {
  const {
    session: { user },
  } = await getSupabaseServer({ protected: true });

  return (
    <UserFeedBoundary userId={user.id}>
      <UserFeed userId={user.id} />
    </UserFeedBoundary>
  );
}
