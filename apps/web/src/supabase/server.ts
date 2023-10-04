import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

interface Params {
  protected: boolean;
}

export const getSupabaseServer = async (params?: Params) => {
  const shouldProtect = params?.protected;
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (shouldProtect && !session) {
    return redirect("/login");
  }

  return { session, supabase };
};
