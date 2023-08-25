/*
  Warnings:

  - You are about to drop the column `id` on the `Embeddings` table. All the data in the column will be lost.
  - You are about to drop the column `metadata` on the `Embeddings` table. All the data in the column will be lost.
  - Added the required column `index` to the `Embeddings` table without a default value. This is not possible if the table is not empty.
  - Added the required column `url` to the `Embeddings` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "vecs"."Embeddings" DROP CONSTRAINT "Embeddings_id_fkey";

-- AlterTable
ALTER TABLE "vecs"."Embeddings" DROP COLUMN "id",
DROP COLUMN "metadata",
ADD COLUMN     "index" INTEGER NOT NULL,
ADD COLUMN     "url" TEXT NOT NULL;

-- AddForeignKey
ALTER TABLE "vecs"."Embeddings" ADD CONSTRAINT "Embeddings_url_fkey" FOREIGN KEY ("url") REFERENCES "public"."Page"("url") ON DELETE RESTRICT ON UPDATE CASCADE;
