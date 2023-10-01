"use client";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import {
  User,
  createClientComponentClient,
} from "@supabase/auth-helpers-nextjs";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Skeleton } from "../ui/skeleton";

interface Props {
  user: User;
}

export function UserNav() {
  const [user, setUser] = useState<User>(undefined);
  const supabase = createClientComponentClient();
  useEffect(() => {
    const setUp = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user) {
        setUser(user);
      }

      // subscribe to changes
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange(async (event, session) => {
        if (!session) {
          setUser(null);
        }
      });

      return () => {
        subscription.unsubscribe();
      };
    };
    setUp();
  }, []);

  const path = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  if (user) {
    const initials = user.email[0].toUpperCase();
    const name = user.user_metadata.full_name;

    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-8 w-8 rounded-full">
            <Avatar className="h-8 w-8">
              <AvatarImage src={user.user_metadata.avatar_url} alt="@shadcn" />
              <AvatarFallback>{initials}</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="end" forceMount>
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
              {name && (
                <p className="truncate text-sm font-medium leading-none">
                  {name}
                </p>
              )}
              <p className="text-muted-foreground truncate text-xs leading-none">
                {user.email}
              </p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem>
              Profile
              <DropdownMenuShortcut>⇧⌘P</DropdownMenuShortcut>
            </DropdownMenuItem>
            <DropdownMenuItem>
              Settings
              <DropdownMenuShortcut>⌘S</DropdownMenuShortcut>
            </DropdownMenuItem>
            <DropdownMenuItem>
              Friends
              <DropdownMenuShortcut>⌘G</DropdownMenuShortcut>
            </DropdownMenuItem>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout}>
            Log out
            <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  // Still getting user data
  if (user === undefined) {
    return <Skeleton className="block h-8 w-8 rounded-full bg-slate-400" />;
  }

  if (path === "/login") {
    return (
      <Link className={cn(buttonVariants({ variant: "link" }))} href="/">
        Feed
      </Link>
    );
  }

  return (
    <Link className={cn(buttonVariants({ variant: "link" }))} href="/login">
      Login
    </Link>
  );
}
