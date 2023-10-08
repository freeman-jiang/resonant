import { NavBar } from "@/components/NavBar/NavBar";
import { Toaster } from "@/components/ui/toaster";
import { cn } from "@/lib/utils";
import { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Resonant",
  description: "A digital feed for the intellectually curious",
};
const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={cn(inter.className, "selection:bg-emerald-200")}>
        <Providers>
          <NavBar />
          <div className="mx-auto px-8 py-4 md:max-w-2xl">
            {children}
            <Toaster />
          </div>
        </Providers>
      </body>
    </html>
  );
}
