"use client";
import { updateUser } from "@/api";
import { USER_QUERY_KEY, useUser } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSupabase } from "@/supabase/client";
import { User } from "@supabase/supabase-js";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { SubmitHandler, useForm } from "react-hook-form";
import { Spinner } from "./Spinner";
import { useToast } from "./ui/use-toast";

type Inputs = {
  firstName: string;
  lastName: string;
};

interface Props {
  user: User;
}

export const Profile = () => {
  const { session } = useSupabase();
  const { data: user } = useUser(session?.user.id);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const defaultValues: Inputs = {
    firstName: user.first_name,
    lastName: user.last_name,
  };
  const { register, handleSubmit } = useForm<Inputs>({
    defaultValues: defaultValues,
  });

  const onSubmit: SubmitHandler<Inputs> = async ({ firstName, lastName }) => {
    mutate({
      id: user.id,
      firstName,
      lastName,
      profileUrl: user.profile_picture_url,
      twitter: user.twitter,
      website: user.website,
    });
    await queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] });
  };

  const { mutate, isPending } = useMutation({
    mutationFn: updateUser,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] });
    },
    onSuccess: () => {
      toast({ title: "Profile updated!" });
    },
    onError: () => {
      toast({ title: "Error updating profile" });
    },
  });

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
        {isPending ? <Spinner /> : "Save"}
      </Button>
    </form>
  );
};
