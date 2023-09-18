-- AlterTable
ALTER TABLE "public"."Page" ADD COLUMN     "depth" INTEGER NOT NULL DEFAULT 0;

UPDATE "Page"
SET depth = ct.depth
FROM "CrawlTask" ct
WHERE "Page"."url" = ct."url";
