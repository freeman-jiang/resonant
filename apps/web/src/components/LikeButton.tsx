"use client";
import { likePage } from "@/api";
import { useSupabase } from "@/supabase";
import { Link } from "@/types/api";
import { Heart } from "lucide-react";
import { Button } from "./ui/button";

interface Props {
  page: Link;
}

export const LikeButton = ({ page }: Props) => {
  const { session, supabase } = useSupabase();
  const user = session.user;

  const handleLike = async () => {
    const res = await likePage(user.id, page.id);
    console.log(res);
  };

  return (
    <Button variant="default" size="sm" onClick={handleLike}>
      <Heart className="mr-2 h-4 w-4" /> Like
    </Button>
  );
};
