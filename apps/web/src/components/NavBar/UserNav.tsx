"use client";
import { useUser } from "@/api/hooks";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useSupabase } from "@/supabase/client";
import { User } from "@supabase/auth-helpers-nextjs";
import Link from "next/link";

interface Props {
  user: User;
}

export function UserNav() {
  const { session, supabase } = useSupabase();
  const { data: user } = useUser(session?.user.id);

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  if (!session) {
    return null;
  }

  if (!user) {
    return null;
  }

  const initials = `${user.first_name[0]}${user.last_name[0]}`;
  const name = `${user.first_name} ${user.last_name}`;

  return (
    <div className="flex items-center gap-4">
      <div className="flex">
        {/* <Link
          href="/friends"
          className={cn(buttonVariants({ variant: "link" }))}
        >
          Friends
        </Link> */}
        <Link href="/liked" className={cn(buttonVariants({ variant: "link" }))}>
          Liked
        </Link>
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-8 w-8 rounded-full">
            <Avatar className="h-8 w-8">
              <AvatarImage src={user.profile_picture_url} alt="@shadcn" />
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="end" forceMount>
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
              <p className="truncate pb-0.5 text-sm font-medium leading-none">
                {name}
              </p>
              <p className="text-muted-foreground truncate pb-0.5 text-xs leading-none">
                {user.email}
              </p>
            </div>
          </DropdownMenuLabel>
          {/* <DropdownMenuSeparator /> */}
          <DropdownMenuGroup>
            <Link href={"/profile"}>
              <DropdownMenuItem>Profile</DropdownMenuItem>
            </Link>
            {/* <DropdownMenuItem>
                Settings
                <DropdownMenuShortcut>⌘S</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem>
                Friends
                <DropdownMenuShortcut>⌘G</DropdownMenuShortcut>
              </DropdownMenuItem> */}
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout}>
            Log out
            {/* <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut> */}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
