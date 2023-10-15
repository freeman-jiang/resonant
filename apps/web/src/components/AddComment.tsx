import { ExistingPageResponse, createComment } from "@/api";
import { PAGE_QUERY_KEY } from "@/api/hooks";
import { useSupabase } from "@/supabase/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageCircle } from "lucide-react";
import { SubmitHandler, useForm } from "react-hook-form";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { useToast } from "./ui/use-toast";

interface Props {
  data: ExistingPageResponse;
}

interface Inputs {
  content: string;
}

export const AddComment = ({ data }: Props) => {
  const { page } = data;
  const { session } = useSupabase();
  const user = session?.user;
  const queryClient = useQueryClient();

  const { mutate } = useMutation({
    mutationFn: (content: string) =>
      createComment({
        content,
        pageId: page.id,
        userId: user.id,
        parentId: null,
      }),
    onSuccess: (newComment) => {
      // Optimistically update the UI
      queryClient.setQueryData<ExistingPageResponse>(
        [PAGE_QUERY_KEY, page.url],
        {
          ...data,
          comments: [newComment, ...data.comments], // since we sort by desc date
        },
      );
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [PAGE_QUERY_KEY, page.url] });
    },
  });

  const { register, handleSubmit } = useForm<Inputs>();
  const { toast } = useToast();

  const onSubmit: SubmitHandler<Inputs> = async ({ content }) => {
    if (!content) {
      toast({
        title: "Comment cannot be empty",
      });
      return;
    }
    mutate(content);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Textarea {...register("content")} />
      <Button
        disabled={!user}
        size="sm"
        className="mt-4 bg-slate-600 hover:bg-slate-600"
        type="submit"
      >
        <MessageCircle className="mr-2 h-4 w-4" /> Comment
      </Button>
    </form>
  );
};
