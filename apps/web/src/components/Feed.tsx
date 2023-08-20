import { ArticleLink } from "@/links";
import { FeedbackButton } from "./FeedbackButton";

export const extractDomain = (url: string) => {
  const domain = url.split("/")[2];
  return domain.split(":")[0];
};

const Entry = ({ title, url, excerpt }: ArticleLink) => {
  return (
    <div className="my-4">
      <div className="flex flex-row items-center justify-between border-b border-slate-400 pb-2">
        <a href={url} className="cursor-pointer" target="_blank">
          <h2 className="scroll-m-20 text-xl font-semibold tracking-tight">
            {title}
          </h2>
          <p className="text-sm font-light text-slate-700">
            {extractDomain(url)}
          </p>
        </a>
        <FeedbackButton className="ml-8 lg:ml-20" />
      </div>
    </div>
  );
};

export const Feed = (props: { links: ArticleLink[] }) => {
  return (
    <div>
      {props.links.map((link) => (
        <Entry key={link.url} {...link} />
      ))}
    </div>
  );
};
