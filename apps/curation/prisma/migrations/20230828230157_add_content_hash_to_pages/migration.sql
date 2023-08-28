/*
  Warnings:

  - A unique constraint covering the columns `[content_hash]` on the table `Page` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `content_hash` to the `Page` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "public"."Page" ADD COLUMN     "content_hash" TEXT NOT NULL;

-- CreateIndex
CREATE UNIQUE INDEX "Page_content_hash_key" ON "public"."Page"("content_hash");
