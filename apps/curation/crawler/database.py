from typing import Optional

import lmdb

from crawler.parse import CrawlResult


class Database:
    def __init__(self):
        self.db = lmdb.open("my_database", map_size=int(1e9))

    def store(self, key: str, value: CrawlResult):
        with self.db.begin(write=True) as txn:
            value_bytes = value.model_dump_json().encode('utf-8')
            key_bytes = key.encode('utf-8')

            if len(value_bytes) > 2 ** 25:
                raise ValueError("Value too large to store in database", value_bytes)
                return

            try:
                txn.put(key_bytes, value_bytes)
            except lmdb.BadValsizeError:
                print("Value too large to store in database", len(value_bytes), len(key_bytes))
                import pdb
                pdb.set_trace()

    def get(self, key: str, default=False) -> Optional[CrawlResult]:
        with self.db.begin() as txn:
            key_bytes = key.encode('utf-8')
            value_bytes = txn.get(key_bytes)
            if default and value_bytes is None:
                return None
            if value_bytes is None:
                raise KeyError("Key not found: " + key)
            return CrawlResult.model_validate_json(value_bytes)

    def contains(self, key: str):
        with self.db.begin() as txn:
            key_bytes = key.encode('utf-8')
            value_bytes = txn.get(key_bytes)
            return value_bytes is not None

    def dump(self):
        # Start a read transaction
        with self.db.begin() as txn:
            # Create a cursor to iterate through the keys
            cursor = txn.cursor()

            # Iterate through the keys and print the values
            for key, value in cursor:
                decoded_value = value.decode("utf-8")  # Convert bytes to string
                print(key)
                # print(f"Key: {key}, Value: {decoded_value}")
