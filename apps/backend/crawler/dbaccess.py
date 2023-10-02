import os
import psycopg
from dotenv import load_dotenv
from psycopg import Connection

load_dotenv()


class DB:
    db: Connection

    def __init__(self):
        self.db = None

    def connect(self):
        self.db = psycopg.connect(os.environ['DATABASE_URL_PG'])

    def transaction(self, *args, **kwargs):
        if self.db is None:
            self.connect()

        return self.db.transaction(*args, **kwargs)

    def cursor(self, *args, **kwargs):
        if self.db is None:
            self.connect()

        return self.db.cursor(*args, **kwargs)

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()


db = DB()
