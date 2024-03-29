import { trackSend } from "@/analytics/mixpanel";
import { sendMessage } from "@/api";
import { usePage, useUserSearch } from "@/api/hooks";
import { useSupabase } from "@/supabase/client";
import { useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "./ui/command";
import { useToast } from "./ui/use-toast";

// TODO: Fix screen flashing on every keypress
interface Props {
  url: string;
}

export function UserSearch({ url }: Props) {
  const [query, setQuery] = useState("");
  const { data: users, isFetching } = useUserSearch(query);
  const { session } = useSupabase();
  const { data, isLoading } = usePage(url, session);
  const { toast } = useToast();

  if (isLoading) {
    return <div>loading</div>;
  }

  if (data.type !== "page") {
    return null;
  }

  const page = data.page;

  const handleSelect = async (id: string, name: string) => {
    await sendMessage({
      pageId: page.id,
      receiverId: id,
      senderId: session.user.id,
    });
    toast({
      title: `Sent link to ${name}`,
      className:
        "fixed top-4 left-[50%] max-h-screen translate-x-[-50%] md:w-fit max-w-[80vw]",
    });
    trackSend();
  };

  const Items = () => {
    if (!users) return null;

    return (
      <>
        {users
          // You can send a link to yourself
          // .filter((user) => user.id !== session.user.id)
          .map((user) => {
            const name = `${user.firstName} ${user.lastName}`;
            const initials = `${user.firstName[0]}${user.lastName[0]}`;

            return (
              <CommandItem
                key={user.id}
                value={user.id}
                onSelect={() => handleSelect(user.id, name)}
              >
                {/* TODO: Optimize with Next.js images */}
                <Avatar className="h-6 w-6">
                  <AvatarImage src={user.profilePictureUrl} />
                  <AvatarFallback>{initials}</AvatarFallback>
                </Avatar>
                <span className="ml-2">{name}</span>
              </CommandItem>
            );
          })}
      </>
    );
  };

  return (
    <Command shouldFilter={false} className="min-h-[20rem]">
      <CommandInput
        placeholder="Search for a user by name..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {!isFetching && <CommandEmpty>No results found</CommandEmpty>}
        {isFetching ? null : <Items />}
        <CommandSeparator />
      </CommandList>
    </Command>
  );
}
