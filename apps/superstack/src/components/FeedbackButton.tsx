import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Ban, Heart, MoreHorizontal, ThumbsUp } from "lucide-react";
export const FeedbackButton = (props: React.HTMLAttributes<HTMLDivElement>) => {
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
          <DropdownMenuItem className="gap-2 cursor-pointer">
            <Heart className="h-4 w-4" />
            Loved this
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2 cursor-pointer">
            <ThumbsUp className="h-4 w-4" />
            Liked this
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2 cursor-pointer">
            <Ban className="h-4 w-4" />
            Not interested
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
