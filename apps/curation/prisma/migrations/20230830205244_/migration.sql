/*
  Warnings:

  - A unique constraint covering the columns `[user_id,page_id,suggested_from_id]` on the table `FeedPage` will be added. If there are existing duplicate values, this will fail.

*/
-- DropIndex
DROP INDEX "public"."FeedPage_user_id_page_id_key";

-- CreateIndex
CREATE UNIQUE INDEX "FeedPage_user_id_page_id_suggested_from_id_key" ON "public"."FeedPage"("user_id", "page_id", "suggested_from_id");
