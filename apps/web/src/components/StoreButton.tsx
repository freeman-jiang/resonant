"use client";
import { storePage } from "@/api";
import { useMutation } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props {
  url: string;
}

const Spinner = () => {
  return (
    <svg
      className="mr-2 h-4 w-4 animate-spin text-white"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
};

export const StoreButton = ({ url }: Props) => {
  const router = useRouter();
  const { toast } = useToast();

  const { mutate, isPending } = useMutation({
    mutationFn: storePage,
    onSuccess: () => {
      router.push(`/c?url=${url}`);
    },
    onError: (error) => {
      toast({ title: "Error storing page" });
    },
  });

  return (
    <Button
      variant="default"
      className="bg-slate-500 hover:bg-slate-600"
      size="sm"
      onClick={() => mutate(url)}
    >
      {isPending ? (
        <>
          <Spinner /> Storing...
        </>
      ) : (
        <>
          <Plus className="mr-2 h-4 w-4" /> Add to Resonant
        </>
      )}
    </Button>
  );
};
