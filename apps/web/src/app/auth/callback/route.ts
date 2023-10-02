import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { getUser } from "./../../../api/index";

import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

// TODO: Add Amplitude sign in tracking here server-side
export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");

  if (code) {
    const supabase = createRouteHandlerClient({ cookies });
    await supabase.auth.exchangeCodeForSession(code);

    const {
      data: { user: supabaseUser },
    } = await supabase.auth.getUser();
    const user = await getUser(supabaseUser.id);
    if (!user) {
      return NextResponse.redirect(`${requestUrl.origin}/new`);
    }
  }
  return NextResponse.redirect(requestUrl.origin);
}
