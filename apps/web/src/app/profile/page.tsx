import { UserBoundary } from "@/api/hooks";
import { Profile } from "@/components/Profile";
import { getSupabaseServer } from "@/supabase/server";

export default async () => {
  const { session } = await getSupabaseServer({ protected: true });

  return (
    <div className="bg mx-auto mt-10 max-w-md">
      <h1 className="text-2xl font-semibold text-slate-900">Profile</h1>
      <UserBoundary session={session}>
        <Profile />
      </UserBoundary>
    </div>
  );
};
