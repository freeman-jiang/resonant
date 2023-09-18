-- CreateTable
CREATE TABLE "public"."User" (
    "id" SERIAL NOT NULL,

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."FeedPage" (
    "id" SERIAL NOT NULL,
    "user_id" INTEGER NOT NULL,
    "page_id" INTEGER NOT NULL,
    "suggested_from_id" INTEGER NOT NULL,

    CONSTRAINT "FeedPage_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "public"."LikedPage" (
    "id" SERIAL NOT NULL,
    "user_id" INTEGER NOT NULL,
    "page_id" INTEGER NOT NULL,

    CONSTRAINT "LikedPage_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "feed_pages_user_id" ON "public"."FeedPage"("user_id");

-- CreateIndex
CREATE INDEX "feed_pages_page_id" ON "public"."FeedPage"("page_id");

-- CreateIndex
CREATE UNIQUE INDEX "FeedPage_user_id_page_id_key" ON "public"."FeedPage"("user_id", "page_id");

-- CreateIndex
CREATE INDEX "liked_pages_user_id" ON "public"."LikedPage"("user_id");

-- CreateIndex
CREATE INDEX "liked_pages_page_id" ON "public"."LikedPage"("page_id");

-- CreateIndex
CREATE UNIQUE INDEX "LikedPage_user_id_page_id_key" ON "public"."LikedPage"("user_id", "page_id");

-- AddForeignKey
ALTER TABLE "public"."FeedPage" ADD CONSTRAINT "FeedPage_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."FeedPage" ADD CONSTRAINT "FeedPage_page_id_fkey" FOREIGN KEY ("page_id") REFERENCES "public"."Page"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."FeedPage" ADD CONSTRAINT "FeedPage_suggested_from_id_fkey" FOREIGN KEY ("suggested_from_id") REFERENCES "public"."LikedPage"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."LikedPage" ADD CONSTRAINT "LikedPage_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."LikedPage" ADD CONSTRAINT "LikedPage_page_id_fkey" FOREIGN KEY ("page_id") REFERENCES "public"."Page"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
