import { sendMessage } from "@/api";
import { usePage, useUserSearch } from "@/api/hooks";
import { useSupabase } from "@/supabase/client";
import { useSearchParams } from "next/navigation";
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
export function UserSearch() {
  const url = useSearchParams().get("url");
  const [query, setQuery] = useState("");
  const { data: users, isFetching } = useUserSearch(query);
  const { session } = useSupabase();
  const { data } = usePage(url, session);
  const { toast } = useToast();

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
    toast({ title: `Sent link to ${name}` });
  };

  const Items = () => {
    if (!users) return null;

    return (
      <>
        {users
          .filter((user) => user.id !== session.user.id)
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
