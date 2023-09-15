"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Ban, Heart, MoreHorizontal, ThumbsUp } from "lucide-react";
import { useToast } from "./ui/use-toast";

enum Feedback {
  Loved,
  Liked,
  NotInterested,
}

const MOCK_ARTICLES: { name: string; url: string }[] = [
  {
    name: "Should We Expect Valuations to Mean-Revert Over Time?",
    url: "https://www.thediff.co/archive/should-we-expect-valuations-to-mean-revert-over-time/",
  },
  {
    name: "reality is unrealistic, take 1",
    url: "https://visakanv.substack.com/p/reality-is-unrealistic-take-1",
  },
  {
    name: "Come for the Network, Pay for the Tool",
    url: "http://subpixel.space/entries/come-for-the-network-pay-for-the-tool/",
  },
];

export const FeedbackButton = (props: React.HTMLAttributes<HTMLDivElement>) => {
  const { toast } = useToast();

  const handleFeedback = (feedback: Feedback) => {
    const relatedArticles = MOCK_ARTICLES;

    const renderRelatedArticles = () => {
      return (
        <div className="w-[90%]">
          {relatedArticles.map((article) => (
            <div className="w-10/12 truncate rounded-md p-1 transition-all hover:bg-sky-100">
              <a href={article.url} target="_blank" className="">
                {article.name}
              </a>
            </div>
          ))}
        </div>
      );
    };

    switch (feedback) {
      case Feedback.Loved:
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
          <DropdownMenuItem className="cursor-pointer gap-2">
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
