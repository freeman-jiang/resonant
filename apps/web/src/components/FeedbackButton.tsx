"use client";
import { trackBroadcast, trackLike } from "@/analytics/mixpanel";
import { Page, likePage, sharePage, unsharePage } from "@/api";
import { GLOBAL_FEED_QUERY_KEY } from "@/api/hooks";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSupabase } from "@/supabase/client";
import { useQueryClient } from "@tanstack/react-query";
import { CircleOff, Heart, MoreHorizontal, Rss } from "lucide-react";
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

  const handleLike = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    await likePage(user.id, page.id);
    trackLike();
    toast({
      title: "Liked! 🎉",
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
            onClick={handleLike}
          >
            <Heart className="h-4 w-4" /> Like this
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
