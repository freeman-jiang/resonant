"use client";
import { likePage } from "@/api";
import { useSupabase } from "@/supabase/client";
import { Page } from "@/types/api";
import { Bookmark } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props {
  page: Page;
}

export const SaveButton = ({ page }: Props) => {
  const { session } = useSupabase();
  const { toast } = useToast();
  const user = session?.user;
  const router = useRouter();

  const handleLike = async () => {
    if (!user) {
      router.push("/login");
      return;
    }
    await likePage(user.id, page.id);
    toast({
      title: "Saved! 🎉",
    });
  };

  return (
    <Button variant="default" size="sm" onClick={handleLike}>
      <Bookmark className="mr-2 h-4 w-4" /> Save
    </Button>
  );
};
