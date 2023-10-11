import { Sender } from "@/api";
import { getRelativeTime } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";

interface Props {
  senders: Sender[];
}

export const Senders = ({ senders }: Props) => {
  // Backend sends order descending for dates (most recent first)
  const mostRecentSender = senders.length > 0 ? senders[0] : null;

  // TODO: Limit number of avatars shown to have +X more
  const renderAvatars = () => {
    // Filter out duplicate senders
    // TODO: This should maybe probably be done on backend
    const senderIds = new Set();

    const avatars = senders
      .filter((sender) => {
        if (senderIds.has(sender.id)) {
          return false;
        }
        senderIds.add(sender.id);
        return true;
      })
      .map((sender) => {
        const initials = `${sender.first_name[0]}${sender.last_name[0]}`;

        return (
          <TooltipProvider delayDuration={0} key={sender.id}>
            <Tooltip>
              <TooltipTrigger className="cursor-default">
                <Avatar className="h-6 w-6">
                  <AvatarImage src={sender.profile_picture_url} />
                  <AvatarFallback className="text-xs">
                    {initials}
                  </AvatarFallback>
                </Avatar>
              </TooltipTrigger>
              <TooltipContent>
                <div className="text-slate-800">{`${sender.first_name} ${sender.last_name}`}</div>
                <div className="text-xs text-slate-500">
                  {getRelativeTime(sender.sent_on)}
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      });

    return <div className="flex -space-x-1.5">{avatars}</div>;
  };

  if (senders.length === 0) {
    return null;
  }
  return (
    <div className="mt-2 text-xs text-slate-500">
      <div className="flex items-center ">
        {renderAvatars()}
        <span className="ml-2">
          Shared {getRelativeTime(mostRecentSender.sent_on)}
        </span>
      </div>
    </div>
  );
};
