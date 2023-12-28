import { RecommendedFeed } from "@/components/feeds/RecommendedFeed";
import { getSupabaseServer } from "@/supabase/server";

export default async () => {
  const {
    session: { user },
  } = await getSupabaseServer({ protected: true });

  return <RecommendedFeed userId={user.id} />;
};
