import { LikedFeedBoundary } from "@/api/hooks";
import { LikedFeed } from "@/components/LikedFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Liked() {
  const { session } = await getSupabaseServer({ protected: true });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Liked</h1>
      <LikedFeedBoundary session={session}>
        <LikedFeed />
      </LikedFeedBoundary>
    </div>
  );
}
