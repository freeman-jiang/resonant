-- CreateIndex
CREATE INDEX ON "vecs"."Embeddings" USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);
