"use client";
import { likePage } from "@/api";
import { useSupabase } from "@/supabase/client";
import { Page } from "@/types/api";
import { Bookmark } from "lucide-react";
import { Button } from "./ui/button";

interface Props {
  page: Page;
}

export const SaveButton = ({ page }: Props) => {
  const { session } = useSupabase();
  const user = session.user;

  const handleLike = async () => {
    await likePage(user.id, page.id);
  };

  return (
    <Button variant="default" size="sm" onClick={handleLike}>
      <Bookmark className="mr-2 h-4 w-4" /> Save
    </Button>
  );
};
