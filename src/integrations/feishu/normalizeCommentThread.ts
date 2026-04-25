export type RawSheetCommentThread = {
  fileToken: string;
  comment: {
    comment_id: string;
    content: string;
    create_time?: string;
    update_time?: string;
    quote?: string;
    anchor?: {
      row?: number;
      column_key?: string;
      sheet_id?: string;
      block_id?: string;
    };
  };
  replies: Array<{
    reply_id: string;
    content: string;
    create_time?: string;
    update_time?: string;
  }>;
};

export type NormalizedCommentThread = {
  fileToken: string;
  commentId: string;
  body: string;
  threadText: string;
  quote: string;
  rowNumber: number | null;
  columnKey: string | null;
  sheetId: string | null;
  blockId: string | null;
  replies: Array<{ replyId: string; content: string }>;
  updatedAt: string | null;
};

export function normalizeCommentThread(input: RawSheetCommentThread): NormalizedCommentThread {
  const body = input.comment.content.trim();
  const replies = input.replies.map((reply) => ({
    replyId: reply.reply_id,
    content: reply.content.trim(),
  }));

  return {
    fileToken: input.fileToken,
    commentId: input.comment.comment_id,
    body,
    threadText: [body, ...replies.map((reply) => reply.content)].filter(Boolean).join("\n"),
    quote: input.comment.quote?.trim() || "",
    rowNumber: input.comment.anchor?.row ?? null,
    columnKey: input.comment.anchor?.column_key ?? null,
    sheetId: input.comment.anchor?.sheet_id ?? null,
    blockId: input.comment.anchor?.block_id ?? null,
    replies,
    updatedAt: input.comment.update_time || input.comment.create_time || null,
  };
}
