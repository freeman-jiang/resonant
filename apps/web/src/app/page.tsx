import { Feed } from "@/components/Feed";

export default function Home() {
  return (
    <div className="mx-auto p-8 lg:max-w-2xl">
      <h1 className="text-3xl font-bold">Superstack</h1>
      <Feed />
    </div>
  );
}
