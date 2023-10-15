import { ExistingPageResponse } from "@/api";
import { AddComment } from "./AddComment";
import { Comment } from "./Comment";

interface Props {
  data: ExistingPageResponse;
}

export const PageComments = ({ data }: Props) => {
  const { comments } = data;

  if (comments.length === 0) {
    return (
      <div className="mt-2">
        <AddComment data={data} />
        <div className="mt-2 text-sm text-slate-500">No comments yet</div>
      </div>
    );
  }

  return (
    <div className="mt-2">
      <AddComment data={data} />
      <div className="mt-4">
        {comments.map((comment) => (
          <Comment key={comment.id} comment={comment} page={data.page} />
        ))}
      </div>
    </div>
  );
};
