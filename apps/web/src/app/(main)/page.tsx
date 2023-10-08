import { UserFeedBoundary } from "@/api/hooks";
import { UserFeed } from "@/components/UserFeed";
import { getSupabaseServer } from "@/supabase/server";
import { redirect } from "next/navigation";

export default async function Home() {
  const { session } = await getSupabaseServer();
  if (!session) {
    redirect("/all");
  }
  const user = session.user;

  return (
    <UserFeedBoundary userId={user.id}>
      <UserFeed userId={user.id} />
    </UserFeedBoundary>
  );
}
