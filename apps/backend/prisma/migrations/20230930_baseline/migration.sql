-- AlterTable
ALTER TABLE "Page" ADD COLUMN ts tsvector
    GENERATED ALWAYS AS
     (setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
     setweight(to_tsvector('english', coalesce(content, '')), 'B')) STORED;


CREATE INDEX ts_idx ON "Page" USING GIN (ts);
