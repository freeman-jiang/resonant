import "@/app/globals.css";
import { Search } from "@/components/Search";
import { Topics } from "@/components/Topics";
import { Toaster } from "@/components/ui/toaster";
import Link from "next/link";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mx-auto p-8 lg:max-w-2xl">
        <Link href="/" className="text-2xl font-bold">
          Superstack
        </Link>
        <Topics />
        <Search />
        {children}
      </div>
      <Toaster />
    </div>
  );
}
