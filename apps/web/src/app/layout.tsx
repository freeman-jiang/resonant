import { Search } from "@/components/Search";
import { Topics } from "@/components/Topics";
import { Toaster } from "@/components/ui/toaster";
import { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Superstack",
  description: "A digital feed for the intellectually curious",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="mx-auto p-8 lg:max-w-2xl">
          <Link href="/" className="text-3xl font-bold">
            Superstack
          </Link>
          <Providers>
            <Topics />
            <Search />
            {children}
          </Providers>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
