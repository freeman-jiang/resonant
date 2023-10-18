import { cn } from "@/lib/utils";
import Link from "next/link";
import { Button, buttonVariants } from "../ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";

export const Feedback = () => {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="link" className="p-0">
          Feedback
        </Button>
      </PopoverTrigger>
      <PopoverContent className="mr-4">
        <div className="text-sm text-slate-500">
          {
            "If you find Resonant useful, run into any issues or have ideas, please email us at: "
          }
          <Link
            href="mailto:resonant.app@gmail.com"
            className={cn(
              buttonVariants({ variant: "link" }),
              "inline p-0 font-medium text-cyan-600",
            )}
          >
            resonant.app@gmail.com
          </Link>
          <div className="mt-2">
            We will personally respond to every message.
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};
