/*
  Warnings:

  - You are about to drop the column `ts` on the `Page` table. All the data in the column will be lost.

*/
-- DropIndex
DROP INDEX "public"."ts_idx";

-- AlterTable
ALTER TABLE "public"."Page" DROP COLUMN "ts";
