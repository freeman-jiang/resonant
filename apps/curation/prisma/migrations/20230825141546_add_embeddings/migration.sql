-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "vecs";
CREATE EXTENSION vector;

-- AlterEnum
ALTER TYPE "public"."TaskStatus" ADD VALUE 'FILTERED';

-- CreateTable
CREATE TABLE "vecs"."embeddings" (
    "id" TEXT NOT NULL,
    "vec" vector(384) NOT NULL,
    "metadata" JSONB NOT NULL,

    CONSTRAINT "embeddings_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "embeddings_id_key" ON "vecs"."embeddings"("id");

-- AddForeignKey
ALTER TABLE "vecs"."embeddings" ADD CONSTRAINT "embeddings_id_fkey" FOREIGN KEY ("id") REFERENCES "public"."Page"("url") ON DELETE RESTRICT ON UPDATE CASCADE;
