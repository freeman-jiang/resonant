"use client";
import {
  Session,
  SupabaseClient,
  createClientComponentClient,
} from "@supabase/auth-helpers-nextjs";
import { useRouter } from "next/navigation";
import {
  ReactNode,
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

interface ContextType {
  session: Session;
  supabase: SupabaseClient;
}

const SupabaseContext = createContext<ContextType>(null as ContextType);

interface ProviderProps {
  session: Session;
  children: ReactNode;
}

export const SupabaseProvider = ({
  children,
  session: serverSession,
}: ProviderProps) => {
  const supabase = createClientComponentClient();
  const router = useRouter();
  const [session, setSession] = useState<Session>(serverSession);

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session);
      if (event === "SIGNED_OUT") {
        router.replace("/login");
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router, supabase]);

  return (
    <SupabaseContext.Provider value={{ session, supabase }}>
      {children}
    </SupabaseContext.Provider>
  );
};

export const useSupabase = () => {
  return useContext(SupabaseContext);
};
