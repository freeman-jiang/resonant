import { Link } from "@/types/api";
import { FeedbackButton } from "./FeedbackButton";

export const extractDomain = (url: string) => {
  const domain = url.split("/")[2];
  return domain.split(":")[0];
};

export const Entry = (link: Link) => {
  return (
    <div className="my-4">
      <div className="flex flex-row items-center justify-between border-b border-slate-400 pb-2">
        <a href={link.url} className="cursor-pointer" target="_blank">
          <h2 className="scroll-m-20 text-xl font-semibold tracking-tight">
            {link.title}
          </h2>
          <p className="text-sm font-light text-slate-700">
            {extractDomain(link.url)}
          </p>
        </a>
        <FeedbackButton link={link} className="ml-8 lg:ml-20" />
      </div>
    </div>
  );
};
