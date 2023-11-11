import { ExistingPageResponse } from "@/api";
import { usePageNodes } from "@/api/hooks";
import { BroadcastButton } from "./BroadcastButton";
import { LikeButton } from "./LikeButton";
import { LinkedBy } from "./LinkedBy";
import { LocalGraph } from "./LocalGraph";
import { PageBox } from "./PageBox";
import { PageComments } from "./PageComments";
import { RelatedFeed } from "./RelatedFeed";
import { SendButton } from "./SendButton";
import { Senders } from "./Senders";

interface Props {
  data: ExistingPageResponse;
}

export const ExistingPage = ({ data: existingPageResponse }: Props) => {
  const { page } = existingPageResponse;
  const { url } = page;
  const { data, error } = usePageNodes(url);

  return (
    <div>
      <PageBox data={page} />
      <div>
        <Senders senders={page.senders} />
        <LinkedBy page={page} />
      </div>
      <div className="mt-4 flex gap-3">
        <SendButton url={url} />
        <BroadcastButton url={url} />
        <LikeButton page={page} />
      </div>
      <div>
        {data && <LocalGraph node={data.node} neighbors={data.neighbors} />}
      </div>
      <div className="mt-4">
        <h2 className="text-xl font-semibold text-slate-900">
          Discussion <span>({existingPageResponse.num_comments})</span>
        </h2>
        <PageComments data={existingPageResponse} />
      </div>
      {/* <SearchBoundary query={url}> */}
      <RelatedFeed url={url} />
      {/* </SearchBoundary> */}
    </div>
  );
};
