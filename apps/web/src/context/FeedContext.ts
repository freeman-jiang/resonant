import { createContext, useContext } from "react";

export const FeedContext = createContext(null);

export const useFeed = () => useContext(FeedContext);