import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { getUser } from "./../../../api/index";

import { AxiosError } from "axios";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");

  if (code) {
    const supabase = createRouteHandlerClient({ cookies });
    await supabase.auth.exchangeCodeForSession(code);

    const {
      data: { user: supabaseUser },
    } = await supabase.auth.getUser();
    try {
      const user = await getUser(supabaseUser.id);
      return NextResponse.redirect(requestUrl.origin);
    } catch (err: unknown) {
      // check if axios error 404
      if (err instanceof AxiosError) {
        if (err.response && err.response.status === 404) {
          // User has been created in Supabase auth but not been created in public schema
          return NextResponse.redirect(`${requestUrl.origin}/new`);
        } else {
          // Big problem
          console.error(err);
          return NextResponse.redirect(requestUrl.origin);
        }
      }
    }
  }
  return NextResponse.redirect(requestUrl.origin);
}
