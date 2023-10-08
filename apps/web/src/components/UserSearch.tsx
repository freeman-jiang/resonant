import { useUserSearch } from "@/api/hooks";
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

interface Inputs {
  query: string;
}

export function UserSearch() {
  const [query, setQuery] = useState("");
  const { data: users, isFetching } = useUserSearch(query);
  console.log(users);

  const handleSelect = (id: string) => {
    console.log(id);
  };

  const Items = () => {
    return (
      <>
        {users?.map((user) => {
          const name = `${user.firstName} ${user.lastName}`;
          const initials = `${user.firstName[0]}${user.lastName[0]}`;
          return (
            <CommandItem key={user.id} value={user.id} onSelect={handleSelect}>
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
