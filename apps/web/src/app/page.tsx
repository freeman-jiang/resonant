import { LINKS } from "@/links";
import { Feed } from "@/components/Feed";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  return (
    <div className="p-8 lg:max-w-2xl mx-auto">
      <h1 className="font-bold text-3xl">Superstack</h1>
      <div className="mt-3 pb-2 flex flex-row gap-2">
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
      <Feed links={LINKS} />
    </div>
  );
}
