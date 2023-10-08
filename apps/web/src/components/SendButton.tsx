"use client";
import { cn } from "@/lib/utils";
import { Send } from "lucide-react";
import { UserSearch } from "./UserSearch";
import { buttonVariants } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";

interface Props extends React.HTMLAttributes<HTMLButtonElement> {
  url: string;
}

export const SendButton = ({ url, ...rest }: Props) => {
  return (
    <Dialog>
      <TooltipProvider>
        <Tooltip>
          <DialogTrigger asChild>
            <TooltipTrigger>
              <p
                className={cn(
                  buttonVariants({ variant: "default", size: "sm" }),
                  "bg-blue-500 hover:bg-blue-600",
                )}
              >
                <Send className="mr-2 h-4 w-4" /> Send
              </p>
            </TooltipTrigger>
          </DialogTrigger>
          <TooltipContent>
            <p>{"Send this link to a specific Resonant user's feed"}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Send link to user</DialogTitle>
          <div className="text-sm text-slate-500">
            It will arrive directly in their feed.
          </div>
          <UserSearch />
        </DialogHeader>
      </DialogContent>
    </Dialog>
  );
};
