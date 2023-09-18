-- CreateSchema
CREATE SCHEMA IF NOT EXISTS "vecs";
CREATE EXTENSION vector;

-- AlterEnum
ALTER TYPE "public"."TaskStatus" ADD VALUE 'FILTERED';

-- CreateTable
CREATE TABLE "vecs"."Embeddings" (
    "id__" SERIAL NOT NULL,
    "id" TEXT NOT NULL,
    "vec" vector(768) NOT NULL,
    "metadata" JSONB NOT NULL,

    CONSTRAINT "Embeddings_pkey" PRIMARY KEY ("id__")
);

-- AddForeignKey
ALTER TABLE "vecs"."Embeddings" ADD CONSTRAINT "Embeddings_id_fkey" FOREIGN KEY ("id") REFERENCES "public"."Page"("url") ON DELETE RESTRICT ON UPDATE CASCADE;
