"use client";
import { trackOnboard } from "@/analytics/mixpanel";
import { CreateUserRequest, createUser } from "@/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User } from "@supabase/auth-helpers-nextjs";
import { useRouter } from "next/navigation";
import { SubmitHandler, useForm } from "react-hook-form";

type Inputs = {
  firstName: string;
  lastName: string;
};

interface Props {
  user: User;
}

// Extract first and last name from full name
// Split from the last space and assume the last word is the last name
const extractNames = (fullName: string | undefined) => {
  if (!fullName) return { firstName: "", lastName: "" };

  const names = fullName.split(" ");
  if (names.length === 1) return { firstName: names[0], lastName: "" };

  const lastName = names.pop();
  const firstName = names.join(" ");
  return { firstName, lastName };
};

export const OnboardingForm = ({ user }: Props) => {
  const defaultValues = extractNames(user.user_metadata?.full_name);
  const { register, handleSubmit } = useForm<Inputs>({ defaultValues });
  const router = useRouter();

  const onSubmit: SubmitHandler<Inputs> = async ({ firstName, lastName }) => {
    const body: CreateUserRequest = {
      id: user.id,
      email: user.email,
      firstName,
      lastName,
      profileUrl: user.user_metadata?.avatar_url,
    };
    await createUser(body);
    trackOnboard(body);
    router.refresh();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
      <div>
        <Label htmlFor="firstName">First Name</Label>
        <Input
          id="firstName"
          placeholder={defaultValues.firstName || ""}
          type="text"
          autoCapitalize="none"
          autoComplete="given-name"
          autoCorrect="off"
          variant="thin"
          {...register("firstName", { required: true })}
        />
      </div>
      <div className="mt-3">
        <Label htmlFor="lastName">Last Name</Label>
        <Input
          id="lastName"
          placeholder={defaultValues.lastName || ""}
          type="text"
          autoCapitalize="none"
          autoComplete="family-name"
          autoCorrect="off"
          variant="thin"
          {...register("lastName", { required: true })}
        />
      </div>
      <Button type="submit" className="mt-4 w-full">
        Finish
      </Button>
    </form>
  );
};
