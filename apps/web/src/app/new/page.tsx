import { getUser } from "@/api";
import { OnboardingForm } from "@/components/OnboardingForm";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function New() {
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const u = await getUser(user.id);
  if (u) {
    redirect("/");
  }

  return (
    <div className="mt-10 flex w-full justify-center">
      <div>
        <div className="text-3xl font-bold">Set up your account</div>
        <div className="mt-1 text-slate-600">
          Give us your name so your friends can find you.
        </div>
        <OnboardingForm user={user} />
      </div>
    </div>
  );
}
