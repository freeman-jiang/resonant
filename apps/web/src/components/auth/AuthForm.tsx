"use client";

import * as React from "react";

import { trackSignIn } from "@/analytics/mixpanel";
import { cn } from "@/lib/utils";
import { createClientComponentClient } from "@supabase/auth-helpers-nextjs";
import { SubmitHandler, useForm } from "react-hook-form";
import { Icons } from "../icons";
import { Button } from "../ui/button";

interface UserAuthFormProps extends React.HTMLAttributes<HTMLDivElement> {}

type Inputs = {
  email: string;
};

export function UserAuthForm({ className, ...props }: UserAuthFormProps) {
  const [isLoading, setIsLoading] = React.useState<boolean>(false);
  const { register, handleSubmit } = useForm<Inputs>();

  const supabase = createClientComponentClient();
  const handleSignInWithEmail = async ({ email }: Inputs) => {
    await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    trackSignIn();
  };

  const handleSignInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
    trackSignIn();
  };

  const onSubmit: SubmitHandler<Inputs> = async (data) => {
    setIsLoading(true);
    await handleSignInWithEmail(data);
    setIsLoading(false);
  };

  return (
    <div className={cn("grid gap-6", className)} {...props}>
      {/* <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid gap-2">
          <div className="flex flex-col space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              placeholder="socrates@athens.com"
              type="email"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect="off"
              disabled={isLoading}
              variant="thin"
              {...register("email", { required: true })}
            />
          </div>
          <Button className="mt-1" disabled={isLoading}>
            {isLoading && (
              <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
            )}
            Sign Up with Email
          </Button>
        </div>
      </form> */}
      {/* <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white px-2">Or continue with</span>
        </div>
      </div> */}
      <Button
        variant="outline"
        type="button"
        disabled={isLoading}
        onClick={handleSignInWithGoogle}
      >
        {isLoading ? (
          <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Icons.googlecolor className="mr-2 h-5 w-5" />
        )}{" "}
        Google
      </Button>
    </div>
  );
}
