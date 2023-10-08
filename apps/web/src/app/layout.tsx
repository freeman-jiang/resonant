import { NavBar } from "@/components/NavBar/NavBar";
import { Toaster } from "@/components/ui/toaster";
import { cn } from "@/lib/utils";
import { SupabaseProvider } from "@/supabase/client";
import { getSupabaseServer } from "@/supabase/server";
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

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { session } = await getSupabaseServer();

  return (
    <html lang="en">
      <body className={cn(inter.className, "selection:bg-emerald-200")}>
        <SupabaseProvider session={session}>
          <Providers>
            <NavBar />
            <div className="mx-auto px-8 py-4 md:max-w-2xl">
              {children}
              <Toaster />
            </div>
          </Providers>
        </SupabaseProvider>
      </body>
    </html>
  );
}
