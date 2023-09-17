/*
  Warnings:

  - A unique constraint covering the columns `[user_id,page_id,suggested_from_id]` on the table `FeedPage` will be added. If there are existing duplicate values, this will fail.

*/
-- DropForeignKey
ALTER TABLE "public"."FeedPage" DROP CONSTRAINT "FeedPage_page_id_fkey";

-- DropForeignKey
ALTER TABLE "public"."FeedPage" DROP CONSTRAINT "FeedPage_suggested_from_id_fkey";

-- DropForeignKey
ALTER TABLE "public"."FeedPage" DROP CONSTRAINT "FeedPage_user_id_fkey";

-- DropForeignKey
ALTER TABLE "public"."LikedPage" DROP CONSTRAINT "LikedPage_page_id_fkey";

-- DropForeignKey
ALTER TABLE "public"."LikedPage" DROP CONSTRAINT "LikedPage_user_id_fkey";

-- DropIndex
DROP INDEX "public"."FeedPage_user_id_page_id_key";

-- CreateIndex
CREATE UNIQUE INDEX "FeedPage_user_id_page_id_suggested_from_id_key" ON "public"."FeedPage"("user_id", "page_id", "suggested_from_id");

-- AddForeignKey
ALTER TABLE "public"."FeedPage" ADD CONSTRAINT "FeedPage_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."FeedPage" ADD CONSTRAINT "FeedPage_page_id_fkey" FOREIGN KEY ("page_id") REFERENCES "public"."Page"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."FeedPage" ADD CONSTRAINT "FeedPage_suggested_from_id_fkey" FOREIGN KEY ("suggested_from_id") REFERENCES "public"."LikedPage"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."LikedPage" ADD CONSTRAINT "LikedPage_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."LikedPage" ADD CONSTRAINT "LikedPage_page_id_fkey" FOREIGN KEY ("page_id") REFERENCES "public"."Page"("id") ON DELETE CASCADE ON UPDATE CASCADE;
