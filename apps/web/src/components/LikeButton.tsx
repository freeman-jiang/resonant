"use client";
import { trackLike } from "@/analytics/mixpanel";
import { Page, likePage } from "@/api";
import { useSupabase } from "@/supabase/client";
import { Heart } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "./ui/button";
import { useToast } from "./ui/use-toast";

interface Props extends React.HTMLAttributes<HTMLButtonElement> {
  page: Page;
}

export const LikeButton = ({ page, ...rest }: Props) => {
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
      title: "Liked! 🎉",
    });
    trackLike();
  };

  return (
    <Button variant="default" size="sm" onClick={handleLike} {...rest}>
      <Heart className="mr-2 h-4 w-4" /> Like
    </Button>
  );
};
