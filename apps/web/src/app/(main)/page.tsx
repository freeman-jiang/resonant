import { UserFeed } from "@/components/UserFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Home() {
  const { session } = await getSupabaseServer();
  const user = session?.user;

  return (
    // <UserFeedBoundary userId={user.id}>
    <UserFeed userId={user?.id} />
    // </UserFeedBoundary>
  );
}
