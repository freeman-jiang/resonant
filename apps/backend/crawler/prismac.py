from typing import Optional, Type, TypeVar, Union

import mmh3
import psycopg
from crawler.config import Config
from prisma.enums import TaskStatus
from prisma.errors import UniqueViolationError
from prisma.models import CrawlTask, Page, User
from prisma.partials import NodePage
from psycopg import Connection, Cursor, sql
from psycopg.rows import class_row, dict_row

from .dbaccess import DB, db
from .link import Link
from .parse import CrawlResult


class PostgresClient:
    conn: DB
    _inner_cursor: Cursor
    cfg: Optional[Config]

    T = TypeVar("T")

    @property
    def _cursor(self) -> Cursor:
        if not hasattr(self, '_inner_cursor'):
            raise RuntimeError("You must call .connect() first!")
        return self._inner_cursor

    @_cursor.setter
    def _cursor(self, value: Cursor):
        self._inner_cursor = value

    def __init__(self, cfg: Optional[Config] = None):
        if cfg is None:
            cfg = Config(empty=True)
        self.cfg = cfg

    def connect(self):
        self.conn = db
        self._cursor = self.conn.cursor(row_factory=dict_row)
        print("Connected to database")

    def cursor(self, row_class: Optional[Type[T]] = None) -> Union[Cursor[T], Cursor[dict]]:

        if row_class:
            cursor = self.conn.cursor(row_factory=class_row(row_class))
        else:
            cursor = self.conn.cursor(row_factory=dict_row)
        return cursor

    def query(self, query: sql.SQL | str, *args):
        self._cursor.execute(query, *args)
        if self._cursor.rowcount > 0:
            return self._cursor.fetchall()

    async def disconnect(self):
        self._cursor.close()
        self.conn.close()

    async def filter_page(self, task: CrawlTask):
        query = sql.SQL('UPDATE "CrawlTask" SET status = %s WHERE id = %s;')
        self._cursor.execute(query, (TaskStatus.FILTERED, task.id))
        self.conn.commit()

    async def fail_page(self, task: CrawlTask):
        query = sql.SQL("UPDATE {} SET status = %s WHERE id = %s;").format(
            sql.Identifier("CrawlTask"))
        self._cursor.execute(query, (TaskStatus.FAILED, task.id))
        self.conn.commit()

    def add_outgoing_links(self, links: list[Link]):
        links_to_add = [l for l in links if l.depth <=
                        self.cfg.max_crawl_depth]
        count = self.add_tasks(links_to_add)
        print(f"PSYCOPG: Added {count} tasks to db")

    def store_raw_page(self, depth: int, crawl_result: CrawlResult) -> Page | None:
        content_hash = str(mmh3.hash128(crawl_result.content, signed=False))

        query = sql.SQL("INSERT INTO {} (content_hash, url, parent_url, title, date, author, content, outbound_urls, depth) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING *;").format(sql.Identifier("Page"))
        self._cursor.execute(query, (content_hash, crawl_result.link.url, crawl_result.link.parent_url, crawl_result.title,
                                     crawl_result.date, crawl_result.author, crawl_result.content, [link.url for link in crawl_result.outbound_links], depth))
        self.conn.commit()

        if self._cursor.rowcount == 0:
            return None
        return Page(**self._cursor.fetchone())

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
        self._cursor.execute(
            query, (TaskStatus.PROCESSING, TaskStatus.PENDING))
        self.conn.commit()

        task = self._cursor.fetchone()
        if task:
            return CrawlTask(**task)
        else:
            return None

    def add_tasks(self, links: list[Link]):
        tasks_data = [{'status': TaskStatus.PENDING, 'url': link.url, 'depth': link.depth,
                       'parent_url': link.parent_url, 'text': link.text} for link in links]

        query = sql.SQL("INSERT INTO \"CrawlTask\" (status, url, depth, parent_url, text) VALUES (%(status)s, %(url)s, %(depth)s, %(parent_url)s, %(text)s) ON CONFLICT DO NOTHING;").format(
            sql.Identifier("CrawlTask"))
        self._cursor.executemany(query, tasks_data)
        self.conn.commit()

        return len(links)

    def finish_task(self, task: CrawlTask):
        query = sql.SQL("UPDATE {} SET status = %s WHERE id = %s;").format(
            sql.Identifier("CrawlTask"))
        self._cursor.execute(query, (TaskStatus.COMPLETED, task.id))
        self.conn.commit()

    async def is_already_explored(self, url: str) -> bool:
        query = sql.SQL("SELECT 1 FROM {} WHERE parent_url = %s LIMIT 1;").format(
            sql.Identifier("CrawlTask"))
        self._cursor.execute(query, (url,))
        return self._cursor.fetchone() is not None

    def get_random_url(self) -> list[Page]:
        random_url_query = sql.SQL(
            """--sql
            SELECT url FROM "Page" WHERE depth < 1 ORDER BY RANDOM() LIMIT 1;""")
        self._cursor.execute(random_url_query)
        url = self._cursor.fetchone()['url']
        return url

    def get_network(self, center_url: str, depth: int) -> list[Page]:
        query = sql.SQL("""--sql
    WITH RECURSIVE PageGraph AS (
    SELECT 1 as depth, p.id, p.title, p.outbound_urls, p.content, p.created_at, p.updated_at, p.url, p.content_hash
    FROM "Page" p
    WHERE p.url = %s
    UNION ALL
    SELECT pg.depth + 1, p.id, p.title, p.outbound_urls, p.content, p.created_at, p.updated_at, p.url, p.content_hash
    FROM "Page" p
    JOIN PageGraph pg ON p.url = ANY(pg.outbound_urls) AND pg.depth < %s
) SELECT * FROM PageGraph;""")
        self._cursor.execute(query, (center_url, depth))
        return [Page(**p) for p in self._cursor.fetchall()]

    def get_page(self, **kwargs) -> Page | None:
        if 'id' in kwargs:
            where_field = 'id'
        elif 'url' in kwargs:
            where_field = 'url'
        else:
            raise Exception("Must specify id or url")
        query = sql.SQL(
            'SELECT * FROM "Page" WHERE {} = %s LIMIT 1;').format(sql.Identifier(where_field))
        self._cursor.execute(query, (kwargs[where_field],))
        page = self._cursor.fetchone()
        if page:
            return Page(**page)
        else:
            return None

    @classmethod
    def _reorder_pages(cls, ids: list[int], pages: list[Page]) -> list[Page]:
        index_hashmap = {id: idx for idx, id in enumerate(ids)}

        # Remains in same order as ids list
        return sorted(pages, key=lambda p: index_hashmap[p.id])

    def get_pages_by_url(self, urls: list[str]) -> list[NodePage]:
        query = sql.SQL(
            'SELECT id, outbound_urls, title, url FROM "Page" WHERE url = ANY(%s);')
        self._cursor.execute(query, (urls,))

        return [NodePage(**p) for p in self._cursor.fetchall()]

    def reverse_find_pages_by_url(self, page_url: str) -> list[NodePage]:
        # Find pages that contain the urls in their outbound_urls
        query = sql.SQL(
            'SELECT id, outbound_urls, title, url FROM "Page" WHERE %s = ANY(outbound_urls);')
        self._cursor.execute(query, (page_url,))

        return [NodePage(**p) for p in self._cursor.fetchall()]

    def get_pages_by_id(self, ids: list[int]) -> list[Page]:
        query = sql.SQL('SELECT * FROM "Page" WHERE id = ANY(%s);')
        self._cursor.execute(query, (ids,))

        return PostgresClient._reorder_pages(ids, [Page(**page) for page in self._cursor.fetchall()])

    def get_page_stubs_by_id(self, ids: list[int]) -> list[Page]:
        query = sql.SQL(
            'SELECT id, title, date, author, created_at, updated_at, outbound_urls, parent_url, url, content_hash, depth, page_rank FROM "Page" WHERE id = ANY(%s);')
        self._cursor.execute(query, (ids,))
        return PostgresClient._reorder_pages(ids, [Page(**page, content='') for page in self._cursor.fetchall()])

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


pg_client = PostgresClient()
