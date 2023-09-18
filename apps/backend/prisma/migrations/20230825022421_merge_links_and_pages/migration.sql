/*
  Warnings:

  - You are about to drop the column `linkId` on the `Page` table. All the data in the column will be lost.
  - You are about to drop the `Link` table. If the table is not empty, all the data it contains will be lost.
  - You are about to drop the `_OutboundLink` table. If the table is not empty, all the data it contains will be lost.
  - A unique constraint covering the columns `[url]` on the table `Page` will be added. If there are existing duplicate values, this will fail.
  - Added the required column `url` to the `Page` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "Page" DROP CONSTRAINT "Page_linkId_fkey";

-- DropForeignKey
ALTER TABLE "_OutboundLink" DROP CONSTRAINT "_OutboundLink_A_fkey";

-- DropForeignKey
ALTER TABLE "_OutboundLink" DROP CONSTRAINT "_OutboundLink_B_fkey";

-- DropIndex
DROP INDEX "Page_linkId_key";

-- AlterTable
ALTER TABLE "Page" DROP COLUMN "linkId",
ADD COLUMN     "outbound_urls" TEXT[],
ADD COLUMN     "parent_url" TEXT,
ADD COLUMN     "url" TEXT NOT NULL;

-- DropTable
DROP TABLE "Link";

-- DropTable
DROP TABLE "_OutboundLink";

-- CreateIndex
CREATE UNIQUE INDEX "Page_url_key" ON "Page"("url");
