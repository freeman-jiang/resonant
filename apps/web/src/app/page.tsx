import { Feed } from "@/components/Feed";
import { Badge } from "@/components/ui/badge";
import { Suspense } from "react";

export default function Home() {
  return (
    <div className="mx-auto p-8 lg:max-w-2xl">
      <h1 className="text-3xl font-bold">Superstack</h1>
      <div className="mt-3 flex flex-row gap-2 pb-2">
        <Badge className="cursor-pointer text-sm">All</Badge>
        <Badge className="cursor-pointer text-sm" variant="outline">
          Software
        </Badge>
        <Badge className="cursor-pointer text-sm" variant="outline">
          Climate
        </Badge>
        <Badge className="cursor-pointer text-sm" variant="outline">
          Philosophy
        </Badge>
      </div>
      <Suspense fallback={<div>loading</div>}>
        <Feed />
      </Suspense>
    </div>
  );
}
