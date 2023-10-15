"use client";
import { Page, PageComment, createComment, deleteComment } from "@/api";
import { PAGE_QUERY_KEY } from "@/api/hooks";
import {
  formatFullName,
  getRelativeTime as formatRelativeTime,
} from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MessageCircle, MoreHorizontal, Trash } from "lucide-react";
import { useState } from "react";
import { SubmitHandler, useForm } from "react-hook-form";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
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
  const commentAuthorName = comment.is_deleted
    ? "[deleted]"
    : formatFullName(author.first_name, author.last_name);
  const initials = `${author.first_name[0]}${author.last_name[0]}`;
  const { register, handleSubmit } = useForm<Inputs>();
  const queryClient = useQueryClient();
  const { session } = useSupabase();
  const user = session?.user;
  const invalidatePage = () => {
    queryClient.invalidateQueries({ queryKey: [PAGE_QUERY_KEY, page.url] });
  };

  const { mutate: trashComment } = useMutation({
    mutationFn: () => deleteComment(comment.id),
    onSettled: () => {
      invalidatePage();
    },
  });

  const handleDelete = () => {
    trashComment();
  };

  const { mutate: addComment } = useMutation({
    mutationFn: (content: string) =>
      createComment({
        content,
        pageId: page.id,
        userId: user.id,
        parentId: comment.id,
      }),
    onSettled: () => {
      invalidatePage();
    },
    onSuccess: () => {
      setOpen(false);
    },
  });

  const onSubmit: SubmitHandler<Inputs> = async ({ content }) => {
    if (!content) {
      return;
    }
    addComment(content);
  };

  const [open, setOpen] = useState(false);

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
    <div className="ml-6 py-3 text-base">
      <div className="relative top-4 border-l pl-4">
        <div className="flex justify-between">
          <div className="flex items-center">
            <p className="mr-3 inline-flex items-center text-sm font-medium text-gray-900 dark:text-white">
              <Avatar className="h-6 w-6">
                <AvatarImage
                  src={comment.is_deleted ? "" : author.profile_picture_url}
                />
                <AvatarFallback className="text-xs">
                  {comment.is_deleted ? "X" : initials}
                </AvatarFallback>
              </Avatar>
              <span className="ml-1.5">{commentAuthorName}</span>
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {formatRelativeTime(comment.created_at)}
            </p>
          </div>
          {user && user.id === comment.author.id && (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <div>
                  <MoreHorizontal className="h-4 w-4" />
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem
                  className="cursor-pointer gap-2"
                  onClick={handleDelete}
                >
                  <Trash className="h-4 w-4" /> Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          {comment.content}
        </p>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button
              variant="link"
              className="p-0 text-slate-700"
              disabled={!user}
            >
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
              {`"${comment.content}"`}
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
    </div>
  );
};
