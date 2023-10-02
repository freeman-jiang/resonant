import { OnboardingForm } from "@/components/OnboardingForm";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";

import { cookies } from "next/headers";

export const dynamic = "force-dynamic";

export default async function New() {
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser();

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
