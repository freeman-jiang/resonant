"use client";
import { createUser } from "@/api";
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
  const lastName = names.pop();
  const firstName = names.join(" ");
  return { firstName, lastName };
};

export const OnboardingForm = ({ user }: Props) => {
  const defaultValues = extractNames(user.user_metadata?.full_name);
  const { register, handleSubmit } = useForm<Inputs>({ defaultValues });
  const router = useRouter();

  const onSubmit: SubmitHandler<Inputs> = async ({ firstName, lastName }) => {
    await createUser({
      id: user.id,
      email: user.email,
      firstName,
      lastName,
    });
    router.replace("/");
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="mt-4">
      <div>
        <Label htmlFor="firstName">First Name</Label>
        <Input
          id="firstName"
          placeholder={defaultValues.firstName || "Marcus"}
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
          placeholder={defaultValues.lastName || "Aurelius"}
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
