"use client";
import { Page, PageComment, createComment } from "@/api";
import { PAGE_QUERY_KEY } from "@/api/hooks";
import {
  formatFullName,
  getRelativeTime as formatRelativeTime,
} from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageCircle } from "lucide-react";
import { SubmitHandler, useForm } from "react-hook-form";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Textarea } from "./ui/textarea";

interface Props {
  comment: PageComment;
  page: Page;
}

interface Inputs {
  content: string;
}

export const Comment = ({ comment, page }: Props) => {
  const { author } = comment;
  const commentAuthorName = formatFullName(author.first_name, author.last_name);
  const { register, handleSubmit } = useForm<Inputs>();
  const queryClient = useQueryClient();
  const {
    session: { user },
  } = useSupabase();

  const { mutate } = useMutation({
    mutationFn: (content: string) =>
      createComment({
        content,
        pageId: page.id,
        userId: user.id,
        parentId: comment.id,
      }),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [PAGE_QUERY_KEY, page.url] });
    },
  });

  const onSubmit: SubmitHandler<Inputs> = async ({ content }) => {
    if (!content) {
      return;
    }
    mutate(content);
  };

  const renderChildren = () => {
    if (comment.children.length === 0) {
      return null;
    }

    return (
      <div className="mt-4">
        {comment.children.map((child) => (
          <Comment key={child.id} comment={child} page={page} />
        ))}
      </div>
    );
  };

  return (
    <div className="ml-6 py-3 text-base dark:bg-gray-900">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center">
          <p className="mr-3 inline-flex items-center text-sm font-semibold text-gray-900 dark:text-white">
            <img
              className="mr-2 h-6 w-6 rounded-full"
              src={author.profile_picture_url}
              alt="Michael Gough"
            />
            {commentAuthorName}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {formatRelativeTime(comment.created_at)}
          </p>
        </div>
      </div>
      <p className="text-gray-500 dark:text-gray-400">{comment.content}</p>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="link" className="p-0 text-slate-700">
            Reply
          </Button>
        </DialogTrigger>
        <DialogContent
          onCloseAutoFocus={(e) => e.preventDefault()}
          className="max-w-lg"
        >
          <DialogHeader>
            <DialogTitle>Reply to: {commentAuthorName}</DialogTitle>
          </DialogHeader>
          <div className="max-w-md truncate text-sm text-slate-500">
            "{comment.content}"
          </div>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Textarea {...register("content")} />
            <Button
              size="sm"
              className="mt-4 bg-slate-600 hover:bg-slate-600/80"
              type="submit"
            >
              <MessageCircle className="mr-2 h-4 w-4" /> Comment
            </Button>
          </form>
        </DialogContent>
      </Dialog>
      {renderChildren()}
    </div>
  );
};
