"use client";

import { Search } from "./Search";
import { Topics } from "./Topics";
interface Props {
  children: React.ReactNode;
}

export const Top = () => {
  return (
    <div>
      <Topics />
      <Search />
    </div>
  );
};
