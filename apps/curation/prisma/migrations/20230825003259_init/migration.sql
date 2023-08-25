-- CreateTable
CREATE TABLE "Link" (
    "id" SERIAL NOT NULL,
    "text" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "parent_url" TEXT NOT NULL,
    "depth" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Link_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Page" (
    "id" SERIAL NOT NULL,
    "title" TEXT,
    "date" TEXT,
    "author" TEXT,
    "content" TEXT NOT NULL,
    "linkId" INTEGER NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Page_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "_OutboundLink" (
    "A" INTEGER NOT NULL,
    "B" INTEGER NOT NULL
);

-- CreateIndex
CREATE UNIQUE INDEX "Link_url_key" ON "Link"("url");

-- CreateIndex
CREATE UNIQUE INDEX "Page_linkId_key" ON "Page"("linkId");

-- CreateIndex
CREATE UNIQUE INDEX "_OutboundLink_AB_unique" ON "_OutboundLink"("A", "B");

-- CreateIndex
CREATE INDEX "_OutboundLink_B_index" ON "_OutboundLink"("B");

-- AddForeignKey
ALTER TABLE "Page" ADD CONSTRAINT "Page_linkId_fkey" FOREIGN KEY ("linkId") REFERENCES "Link"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_OutboundLink" ADD CONSTRAINT "_OutboundLink_A_fkey" FOREIGN KEY ("A") REFERENCES "Link"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "_OutboundLink" ADD CONSTRAINT "_OutboundLink_B_fkey" FOREIGN KEY ("B") REFERENCES "Page"("id") ON DELETE CASCADE ON UPDATE CASCADE;
