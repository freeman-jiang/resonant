/*
  Warnings:

  - You are about to drop the column `updated_at` on the `Rss` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "public"."Rss" DROP COLUMN "updated_at",
ADD COLUMN     "last_crawled_at" TIMESTAMPTZ NOT NULL DEFAULT '2000-01-01 01:01:00.520 +00:00';
