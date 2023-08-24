import json
from typing import Optional, TypeVar, Type

import lmdb
from pydantic import BaseModel

from crawler.parse import CrawlResult

T = TypeVar('T', bound=BaseModel)


class Database:
    db: lmdb.Environment
    value_type: T

    def __init__(self, value_type: Type[T], name="my_database"):
        self.value_type = value_type
        self.db = lmdb.open(name, map_size=int(1e9))

    def store(self, key: str, value: T):
        with self.db.begin(write=True) as txn:
            value_bytes = value.json().encode('utf-8')
            key_bytes = key.encode('utf-8')

            if len(value_bytes) > 2 ** 25:
                raise ValueError(
                    "Value too large to store in database", value_bytes)
                return

            try:
                txn.put(key_bytes, value_bytes)
            except lmdb.BadValsizeError:
                print("Value too large to store in database",
                      len(value_bytes), len(key_bytes))
                import pdb
                pdb.set_trace()

    def get(self, key: str, allow_null: bool = False) -> Optional[T]:
        with self.db.begin() as txn:
            key_bytes = key.encode('utf-8')
            value_bytes = txn.get(key_bytes)
            if allow_null and value_bytes is None:
                return None
            if value_bytes is None:
                raise KeyError("Key not found: " + key)
            return self.value_type.model_validate_json(value_bytes)

    def contains(self, key: str):
        with self.db.begin() as txn:
            key_bytes = key.encode('utf-8')
            value_bytes = txn.get(key_bytes)
            return value_bytes is not None

    # Dump contents of the db in human readable format to "dump.txt"

    def dump_to_file(self):
        with self.db.begin() as txn:
            cursor = txn.cursor()

            with open("dump.txt", "w") as f:
                for key, value in cursor:
                    decoded_value = value.decode("utf-8")
                    f.write(f"Key: {key}\n\nValue: {decoded_value}\n\n\n")

    def dump_json(self):
        with self.db.begin() as txn:
            cursor = txn.cursor()
            js = {}
            for key, value in cursor:
                decoded_value = value.decode("utf-8")
                decoded_key = key.decode("utf-8")
                js[decoded_key] = decoded_value

            json.dump(js, open("dump.json", "w"), indent=4)


def test_dump_db():
    db = Database(CrawlResult)
    db.dump_json()
