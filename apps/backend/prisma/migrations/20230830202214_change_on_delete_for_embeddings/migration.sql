-- DropForeignKey
ALTER TABLE "vecs"."Embeddings" DROP CONSTRAINT "Embeddings_url_fkey";

-- CreateTable
CREATE TABLE "public"."Topic" (
    "id" SERIAL NOT NULL,
    "name" TEXT NOT NULL,
    "embedding" vector(768) NOT NULL,

    CONSTRAINT "Topic_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Topic_name_key" ON "public"."Topic"("name");

-- AddForeignKey
ALTER TABLE "vecs"."Embeddings" ADD CONSTRAINT "Embeddings_url_fkey" FOREIGN KEY ("url") REFERENCES "public"."Page"("url") ON DELETE CASCADE ON UPDATE CASCADE;
