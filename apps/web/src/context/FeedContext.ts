import { Link } from "@/types/api";
import { createContext, useContext } from "react";

interface Context {
  setLinks: (links: Link[]) => void;
}

export const FeedContext = createContext<Context>(null);

export const useFeed = () => useContext(FeedContext);
