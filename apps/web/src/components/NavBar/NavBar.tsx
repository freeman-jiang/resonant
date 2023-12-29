import { UserBoundary } from "@/api/hooks";
import { getSupabaseServer } from "@/supabase/server";
import { Share2, Waypoints } from "lucide-react";
import Link from "next/link";
import { Button } from "../ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { RightButton } from "./RightButton";
import { UserNav } from "./UserNav";

export const dynamic = "force-dynamic";

export async function NavBar({
  className,
  ...props
}: React.HTMLAttributes<HTMLElement>) {
  const { session } = await getSupabaseServer();
  return (
    <div className="border-b" id="navbar">
      <div className="flex h-16 items-center justify-between px-4">
        <Link href="/" className="text-xl font-semibold">
          Resonant
        </Link>

        <div className="flex items-center">
          {/* <Link
            className={cn(buttonVariants({ variant: "link" }))}
            href="/graph"
          >
            Graph
          </Link> */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary">Graphs</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              {/* <DropdownMenuLabel>Select a graph</DropdownMenuLabel> */}
              {/* <DropdownMenuSeparator /> */}
              <DropdownMenuRadioGroup>
                <Link href="/graph">
                  <DropdownMenuRadioItem
                    value="bottom"
                    className="cursor-pointer p-1"
                  >
                    <Share2 className="mr-3 h-5 w-5" />
                    Graph
                  </DropdownMenuRadioItem>
                </Link>
                <Link href="/big-graph">
                  <DropdownMenuRadioItem
                    value="right"
                    className="cursor-pointer p-1"
                  >
                    <Waypoints className="mr-3 h-5 w-5" />
                    Big Graph
                  </DropdownMenuRadioItem>
                </Link>
              </DropdownMenuRadioGroup>
            </DropdownMenuContent>
          </DropdownMenu>
          <UserBoundary session={session}>
            <UserNav />
            <RightButton />
          </UserBoundary>
        </div>
      </div>
    </div>
  );
}
