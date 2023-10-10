"use client";
import { trackBroadcast, trackSave } from "@/analytics/mixpanel";
import { Page, savePage, sharePage, unsharePage } from "@/api";
import { GLOBAL_FEED_QUERY_KEY } from "@/api/hooks";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSupabase } from "@/supabase/client";
import { useQueryClient } from "@tanstack/react-query";
import { Bookmark, CircleOff, MoreHorizontal, Rss } from "lucide-react";
import { useRouter } from "next/navigation";
import { useToast } from "./ui/use-toast";

enum Feedback {
  Loved,
  Liked,
  NotInterested,
}

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  page: Page;
  canUnsend?: boolean;
}

export const FeedbackButton = ({ canUnsend, page, ...props }: Props) => {
  const { session } = useSupabase();
  const user = session?.user;
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const router = useRouter();

  const handleSave = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    await savePage(user.id, page.id);
    trackSave();
    toast({
      title: "Saved! 🎉",
    });
  };

  const handleShare = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    await sharePage(user.id, page.id);
    trackBroadcast();
    queryClient.invalidateQueries({ queryKey: [GLOBAL_FEED_QUERY_KEY] });
    toast({ title: "Broadcasted! 🎉" });
  };

  const handleUnshare = async () => {
    await unsharePage(user.id, page.id);
    queryClient.invalidateQueries({ queryKey: [GLOBAL_FEED_QUERY_KEY] });
    toast({ title: "Unbroadcasted! 🎉" });
  };

  const Share = () => {
    // TODO: Fix this for For You page not working
    if (canUnsend) {
      return (
        <DropdownMenuItem
          className="cursor-pointer gap-2"
          onClick={handleUnshare}
        >
          <CircleOff className="h-4 w-4" /> Unbroadcast this
        </DropdownMenuItem>
      );
    }

    return (
      <DropdownMenuItem className="cursor-pointer gap-2" onClick={handleShare}>
        <Rss className="h-4 w-4" /> Broadcast this
      </DropdownMenuItem>
    );
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
          <Share />
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
