import { AddPage } from "@/components/AddPage";

interface RouteParams {
  searchParams: {
    url: string;
  };
}

export default async function Add(params: RouteParams) {
  const { url } = params.searchParams;

  return <AddPage url={url} />;
}
