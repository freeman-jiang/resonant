import { PageBoundary } from "@/api/hooks";
import { PageLayout } from "@/components/PageLayout";
import { getSupabaseServer } from "@/supabase/server";

interface RouteParams {
  searchParams: {
    url: string;
  };
}

export default async function Page(params: RouteParams) {
  const { url } = params.searchParams;
  const { session } = await getSupabaseServer();

  return (
    <PageBoundary session={session} url={url}>
      <PageLayout url={url} session={session} />
    </PageBoundary>
  );
}
