import { ExistingPageResponse } from "@/api";
import { BroadcastButton } from "./BroadcastButton";
import { LikeButton } from "./LikeButton";
import { LinkedBy } from "./LinkedBy";
import { PageBox } from "./PageBox";
import { PageComments } from "./PageComments";
import { RelatedFeed } from "./RelatedFeed";
import { SendButton } from "./SendButton";
import { Senders } from "./Senders";

interface Props {
  data: ExistingPageResponse;
}

export const ExistingPage = ({ data }: Props) => {
  const { page } = data;
  const { url } = page;

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
      <div className="mt-4">
        <h2 className="text-xl font-semibold text-slate-900">
          Discussion <span>({data.num_comments})</span>
        </h2>
        <PageComments data={data} />
      </div>
      {/* <SearchBoundary query={url}> */}
      <RelatedFeed url={url} />
      {/* </SearchBoundary> */}
    </div>
  );
};
