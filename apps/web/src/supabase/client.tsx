"use client";
import {
  Session,
  SupabaseClient,
  createClientComponentClient,
} from "@supabase/auth-helpers-nextjs";
import { ReactNode, createContext, useContext } from "react";

interface ContextType {
  session: Session;
  supabase: SupabaseClient;
}

const SupabaseContext = createContext<ContextType>(null as ContextType);

interface ProviderProps {
  session: Session;
  children: ReactNode;
}

export const SupabaseProvider = ({ children, session }: ProviderProps) => {
  const supabase = createClientComponentClient();

  // useEffect(() => {
  //   const {
  //     data: { subscription },
  //   } = supabase.auth.onAuthStateChange((event, session) => {
  //     if (!session) {
  //       router.push("/login");
  //     }
  //     router.refresh();
  //   });

  //   return () => {
  //     subscription.unsubscribe();
  //   };
  // }, [router, supabase]);

  return (
    <SupabaseContext.Provider value={{ session, supabase }}>
      {children}
    </SupabaseContext.Provider>
  );
};

export const useSupabase = () => {
  return useContext(SupabaseContext);
};
