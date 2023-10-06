import { NavBar } from "@/components/NavBar/NavBar";
import { cn } from "@/lib/utils";
import { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

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
        <NavBar />
        {children}
      </body>
    </html>
  );
}
