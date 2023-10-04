"use client";
import { likePage } from "@/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSupabase } from "@/supabase/client";
import { Page } from "@/types/api";
import { Bookmark, MoreHorizontal } from "lucide-react";
import { useToast } from "./ui/use-toast";

enum Feedback {
  Loved,
  Liked,
  NotInterested,
}

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  page: Page;
}

export const FeedbackButton = ({ page, ...props }: Props) => {
  const {
    session: { user },
  } = useSupabase();
  const { toast } = useToast();

  const handleSave = async () => {
    await likePage(user.id, page.id);
    toast({
      title: "Saved! 🎉",
    });
  };

  return (
    <div {...props}>
      <DropdownMenu>
        <DropdownMenuTrigger>
          <div>
            <span className="sr-only">Give feedback on article relevancy</span>
            <MoreHorizontal className="h-4 w-4" />
          </div>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem
            className="cursor-pointer gap-2"
            onClick={handleSave}
          >
            <Bookmark className="h-4 w-4" /> Save this
          </DropdownMenuItem>
          {/* <DropdownMenuItem
            className="cursor-pointer gap-2"
            onClick={() => handleFeedback(Feedback.Loved)}
          >
            <Heart className="h-4 w-4" />
            Loved this
          </DropdownMenuItem>
          <DropdownMenuItem
            className="cursor-pointer gap-2"
            onClick={() => handleFeedback(Feedback.Liked)}
          >
            <ThumbsUp className="h-4 w-4" />
            Liked this
          </DropdownMenuItem>
          <DropdownMenuItem className="cursor-pointer gap-2">
            <Ban className="h-4 w-4" />
            Not interested
          </DropdownMenuItem> */}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
