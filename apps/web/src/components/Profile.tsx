"use client";
import { updateUser } from "@/api";
import { USER_QUERY_KEY, useUser } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { SubmitHandler, useForm } from "react-hook-form";
import { Spinner } from "./Spinner";
import { useToast } from "./ui/use-toast";

type Inputs = {
  firstName: string;
  lastName: string;
};

interface Props {
  userId: string;
}

export const Profile = ({ userId }: Props) => {
  const { data: user } = useUser(userId);
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
      id: userId,
      firstName,
      lastName,
      profileUrl: user.profile_picture_url,
      twitter: user.twitter,
      website: user.website,
    });
  };

  const { mutate, isPending } = useMutation({
    mutationFn: updateUser,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] });
    },
    onSuccess: () => {
      console.log("success");
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
        {isPending ? <Spinner /> : "Update"}
      </Button>
    </form>
  );
};
