"use client";
import { sharePage } from "@/api";
import { useSupabase } from "@/supabase/client";
import { Page } from "@/types/api";
import { SendHorizonal } from "lucide-react";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props extends React.HTMLAttributes<HTMLButtonElement> {
  page: Page;
}

export const ShareButton = ({ page, ...rest }: Props) => {
  const { session } = useSupabase();
  const user = session?.user;

  const { toast } = useToast();
  const handleShare = async () => {
    await sharePage(user.id, page.id);
    toast({ title: "Shared!" });
  };

  return (
    <Button
      variant="default"
      className="bg-emerald-500 hover:bg-emerald-400"
      size="sm"
      onClick={handleShare}
      {...rest}
    >
      <SendHorizonal className="mr-2 h-4 w-4" /> Share
    </Button>
  );
};
