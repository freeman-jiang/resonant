import { fetchFeed } from "@/api";
import { Feed } from "@/components/Feed";

export default async function Home() {
  const links = await fetchFeed();

  return (
    <div className="mx-auto p-8 lg:max-w-2xl">
      <h1 className="text-3xl font-bold">Superstack</h1>
      <Feed links={links} />
    </div>
  );
}
