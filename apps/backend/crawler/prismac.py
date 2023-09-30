from typing import Optional

import mmh3
import psycopg
from crawler.config import Config
from prisma.enums import TaskStatus
from prisma.errors import UniqueViolationError
from prisma.models import CrawlTask, Page
from psycopg import Connection, Cursor, sql
from psycopg.rows import dict_row

from .dbaccess import DB, db
from .link import Link
from .parse import CrawlResult


class PrismaClient:
    conn: DB
    cursor: Cursor
    cfg: Optional[Config]

    def __init__(self, cfg: Optional[Config]):
        self.cfg = cfg

    def connect(self):
        self.conn = db
        self.cursor = self.conn.cursor(row_factory=dict_row)
        print("Connected to database")

    def query(self, query: sql.SQL | str, *args):
        self.cursor.execute(query, *args)
        return self.cursor.fetchall()

    async def disconnect(self):
        self.cursor.close()
        self.conn.close()

    async def filter_page(self, task: CrawlTask):
        query = sql.SQL('UPDATE "CrawlTask" SET status = %s WHERE id = %s;')
        self.cursor.execute(query, (TaskStatus.FILTERED, task.id))
        self.conn.commit()

    async def fail_page(self, task: CrawlTask):
        query = sql.SQL("UPDATE {} SET status = %s WHERE id = %s;").format(
            sql.Identifier("CrawlTask"))
        self.cursor.execute(query, (TaskStatus.FAILED, task.id))
        self.conn.commit()

    def add_outgoing_links(self, links: list[Link]):
        links_to_add = [l for l in links if l.depth <=
                        self.cfg.max_crawl_depth]
        count = self.add_tasks(links_to_add)
        print(f"PSYCOPG: Added {count} tasks to db")

    def store_raw_page(self, depth: int, crawl_result: CrawlResult) -> Page | None:
        content_hash = str(mmh3.hash128(crawl_result.content, signed=False))

        query = sql.SQL("INSERT INTO {} (content_hash, url, parent_url, title, date, author, content, outbound_urls, depth) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING *;").format(sql.Identifier("Page"))
        self.cursor.execute(query, (content_hash, crawl_result.link.url, crawl_result.link.parent_url, crawl_result.title,
                            crawl_result.date, crawl_result.author, crawl_result.content, [link.url for link in crawl_result.outbound_links], depth))
        self.conn.commit()

        if self.cursor.rowcount == 0:
            return None
        return Page(**self.cursor.fetchone())

    def store_page(self, task: CrawlTask, crawl_result: CrawlResult) -> Optional[Page]:
        try:
            page = self.store_raw_page(task.depth, crawl_result)
            self.finish_task(task)
            self.add_outgoing_links(crawl_result.outbound_links)
            return page
        except UniqueViolationError:
            print(f"EXCEPTION! Page already exists: {crawl_result.link.url}")
            return None

    async def get_task(self) -> CrawlTask | None:
        query = sql.SQL("UPDATE {} SET status = %s WHERE id = (SELECT id FROM {} WHERE status::text = %s ORDER BY depth ASC, boost DESC, id ASC FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *;").format(
            sql.Identifier("CrawlTask"), sql.Identifier("CrawlTask"))
        self.cursor.execute(query, (TaskStatus.PROCESSING, TaskStatus.PENDING))
        self.conn.commit()

        task = self.cursor.fetchone()
        if task:
            return CrawlTask(**task)
        else:
            return None

    def add_tasks(self, links: list[Link]):
        tasks_data = [{'status': TaskStatus.PENDING, 'url': link.url, 'depth': link.depth,
                       'parent_url': link.parent_url, 'text': link.text} for link in links]

        query = sql.SQL("INSERT INTO \"CrawlTask\" (status, url, depth, parent_url, text) VALUES (%(status)s, %(url)s, %(depth)s, %(parent_url)s, %(text)s) ON CONFLICT DO NOTHING;").format(
            sql.Identifier("CrawlTask"))
        self.cursor.executemany(query, tasks_data)
        self.conn.commit()

        return len(links)

    def finish_task(self, task: CrawlTask):
        query = sql.SQL("UPDATE {} SET status = %s WHERE id = %s;").format(
            sql.Identifier("CrawlTask"))
        self.cursor.execute(query, (TaskStatus.COMPLETED, task.id))
        self.conn.commit()

    async def is_already_explored(self, url: str) -> bool:
        query = sql.SQL("SELECT 1 FROM {} WHERE parent_url = %s LIMIT 1;").format(
            sql.Identifier("CrawlTask"))
        self.cursor.execute(query, (url,))
        return self.cursor.fetchone() is not None

    async def get_page(self, url: str) -> Page | None:
        query = sql.SQL("SELECT * FROM {} WHERE url = %s LIMIT 1;").format(
            sql.Identifier("Page"))
        self.cursor.execute(query, (url,))
        page = self.cursor.fetchone()
        if page:
            return Page(**page)
        else:
            return None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()
