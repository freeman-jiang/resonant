"use client";
import { addPage } from "@/api";
import { PAGE_QUERY_KEY } from "@/api/hooks";
import { useSupabase } from "@/supabase/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
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
  const { toast } = useToast();
  const { session } = useSupabase();
  const queryClient = useQueryClient();

  const { mutate, isPending } = useMutation({
    mutationFn: (url: string) => {
      return addPage(session.user.id, url);
    },
    onError: (error) => {
      toast({ title: "Error storing page" });
    },
    onSuccess: async (page) => {
      toast({ title: "Page saved!" });
      queryClient.invalidateQueries({
        queryKey: [PAGE_QUERY_KEY, url],
      });
    },
  });

  return (
    <Button
      variant="default"
      className="bg-slate-500 hover:bg-slate-600"
      size="sm"
      onClick={() => {
        mutate(url);
      }}
      disabled={!session}
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
