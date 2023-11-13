"use client";
import { usePageNodes } from "@/api/hooks";

export default function Page() {
  const { data } = usePageNodes("https://hypertext.joodaloop.com/");

  return null;
}
