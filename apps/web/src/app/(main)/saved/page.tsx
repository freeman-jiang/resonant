import { SavedFeedBoundary } from "@/api/hooks";
import { SavedFeed } from "@/components/SavedFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Liked() {
  const { session } = await getSupabaseServer({ protected: true });

  return (
    <div className="mt-5">
      <h1 className="text-2xl font-semibold text-slate-900">Saved</h1>
      <SavedFeedBoundary session={session}>
        <SavedFeed />
      </SavedFeedBoundary>
    </div>
  );
}
