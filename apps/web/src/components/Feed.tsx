import { Link } from "@/types/api";
import { Entry } from "./Entry";

async function getData() {
  const response = await fetch("http://127.0.0.1:8000/pages", {
    cache: "no-store",
    next: {
      tags: ["pages"],
      // revalidate: 30, // Clear cache every 30 seconds
    },
  });
  return response.json() as Promise<Link[]>;
}

export const Feed = async () => {
  const links = await getData();

  return (
    <div>
      {links.map((link) => (
        <Entry key={link.url} {...link} />
      ))}
    </div>
  );
};
