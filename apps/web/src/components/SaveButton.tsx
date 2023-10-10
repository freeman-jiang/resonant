"use client";
import { trackSave } from "@/analytics/amplitude";
import { Page, savePage } from "@/api";
import { useSupabase } from "@/supabase/client";
import { Bookmark } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props extends React.HTMLAttributes<HTMLButtonElement> {
  page: Page;
}

export const SaveButton = ({ page, ...rest }: Props) => {
  const { session } = useSupabase();
  const { toast } = useToast();
  const user = session?.user;
  const router = useRouter();

  const handleLike = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    await savePage(user.id, page.id);
    toast({
      title: "Saved! 🎉",
    });
    trackSave();
  };

  return (
    <Button variant="default" size="sm" onClick={handleLike} {...rest}>
      <Bookmark className="mr-2 h-4 w-4" /> Save
    </Button>
  );
};
