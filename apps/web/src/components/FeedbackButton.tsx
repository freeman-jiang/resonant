"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Link } from "@/types/api";
import { Ban, Heart, MoreHorizontal, ThumbsUp } from "lucide-react";
import { useToast } from "./ui/use-toast";

enum Feedback {
  Loved,
  Liked,
  NotInterested,
}

const getRelatedArticles = async ({ id }: Link) => {
  const response = await fetch(
    `http://127.0.0.1:8000/like/${Math.floor(Math.random() * 1000)}/${id}`,
  );

  if (!response.ok) {
    throw new Error("Failed to fetch data");
  }

  return response.json() as Promise<Link[]>;
};

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  link: Link;
}

export const FeedbackButton = ({ link, ...props }: Props) => {
  const { toast } = useToast();

  const handleFeedback = async (feedback: Feedback) => {
    const relatedArticles = await getRelatedArticles(link);
    console.log("relatedArticles", relatedArticles);

    const renderRelatedArticles = () => {
      return (
        <div className="w-[90%]">
          {relatedArticles.map((article) => (
            <div
              key={article.url}
              className="w-10/12 truncate rounded-md p-1 transition-all hover:bg-sky-100"
            >
              <a href={article.url} target="_blank" className="">
                {article.title}
              </a>
            </div>
          ))}
        </div>
      );
    };

    switch (feedback) {
      case Feedback.Liked:
        toast({
          title: "Here are 3 similar articles you might like",
          description: renderRelatedArticles(),
        });
        break;
    }
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
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
