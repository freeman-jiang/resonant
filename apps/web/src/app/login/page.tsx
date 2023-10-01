import { UserAuthForm } from "@/components/auth/AuthForm";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function AuthenticationPage() {
  const supabase = createServerComponentClient({ cookies });
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (session) {
    redirect("/");
  }

  return (
    <div className="mt-10 flex w-full justify-center px-4">
      <div className="flex flex-col">
        <div className="text-3xl font-bold">Stop doomscrolling.</div>
        <div className="text-slate-600">
          Join a collaborative digital feed curated by your friends.
        </div>
        <div className="mt-20 self-center">
          <div className="flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
            <div className="flex flex-col text-center">
              <h1 className="text-2xl font-semibold tracking-tight">
                Create an account
              </h1>
              <p className="text-sm text-slate-600">
                Enter your email below to create your account
              </p>
            </div>
            <UserAuthForm />
            {/* <p className="text-muted-foreground px-8 text-center text-sm">
              By clicking continue, you agree to our{" "}
              <Link
                href="/terms"
                className="hover:text-primary underline underline-offset-4"
              >
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link
                href="/privacy"
                className="hover:text-primary underline underline-offset-4"
              >
                Privacy Policy
              </Link>
              .
            </p> */}
          </div>
        </div>
      </div>
    </div>
  );
}
