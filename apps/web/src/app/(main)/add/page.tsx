import { crawlInteractive } from "@/api";
import { AddPage } from "@/components/AddPage";

interface RouteParams {
  searchParams: {
    url: string;
  };
}

export default async function Add(params: RouteParams) {
  const { url } = params.searchParams;
  const s = await crawlInteractive(url);
  console.log(s);

  return (
    // <CrawlBoundary url={url}>
    <AddPage url={url} />
    // </CrawlBoundary>
  );
}
