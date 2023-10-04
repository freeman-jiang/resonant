import { getSavedPages } from "@/api";
import { Feed } from "@/components/Feed";
import { getSupabaseServer } from "@/supabase/server";

export default async function Liked() {
  const { session } = await getSupabaseServer();
  const { user } = session;

  const pages = await getSavedPages(user.id);

  return (
    <div className="mt-5">
      <h1 className="text-2xl font-semibold text-slate-900">Saved</h1>
      <Feed feed={pages} />
    </div>
  );
}
