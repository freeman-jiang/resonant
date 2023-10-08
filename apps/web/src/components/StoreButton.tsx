"use client";
import { addPage } from "@/api";
import { PAGE_QUERY_KEY } from "@/api/hooks";
import { useSupabase } from "@/supabase/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { Spinner } from "./Spinner";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props {
  url: string;
}

export const StoreButton = ({ url }: Props) => {
  const { toast } = useToast();
  const { session } = useSupabase();
  const queryClient = useQueryClient();
  const router = useRouter();

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
      router.replace(`/c?url=${page.url}`);
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
