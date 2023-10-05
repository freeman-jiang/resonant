"use client";
import { sharePage, unsharePage } from "@/api";
import { PAGE_QUERY_KEY, usePage } from "@/api/hooks";
import { useSupabase } from "@/supabase/client";
import { useQueryClient } from "@tanstack/react-query";
import { CircleOff, Send } from "lucide-react";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props extends React.HTMLAttributes<HTMLButtonElement> {
  url: string;
}

export const ShareButton = ({ url, ...rest }: Props) => {
  const { session } = useSupabase();
  const {
    data: { page, sender },
  } = usePage(url, session);
  const user = session?.user;
  const queryClient = useQueryClient();

  const { toast } = useToast();
  const handleShare = async () => {
    await sharePage(user.id, page.id);
    toast({ title: "Broadcasted! 🎉" });
    queryClient.invalidateQueries({ queryKey: [PAGE_QUERY_KEY, url] });
  };

  const handleUnshare = async () => {
    await unsharePage(user.id, page.id);
    toast({ title: "Unbroadcasted! 🎉" });
    queryClient.invalidateQueries({ queryKey: [PAGE_QUERY_KEY, url] });
  };

  const shouldUnshare = user && sender && user.id === sender.id;

  if (shouldUnshare) {
    return (
      <Button
        variant="default"
        className="bg-slate-500 hover:bg-slate-600"
        size="sm"
        onClick={handleUnshare}
        {...rest}
      >
        <CircleOff className="mr-2 h-4 w-4" /> Unbroadcast
      </Button>
    );
  }

  return (
    <Button
      variant="default"
      className="bg-emerald-500 hover:bg-emerald-400"
      size="sm"
      onClick={handleShare}
      {...rest}
    >
      <Send className="mr-2 h-4 w-4" /> Broadcast
    </Button>
  );
};
