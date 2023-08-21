from typing import Optional

import lmdb

from crawler.parse import CrawlResult


class Database:
    db: lmdb.Environment

    def __init__(self):
        self.db = lmdb.open("my_database", map_size=int(1e9))

    def store(self, key: str, value: CrawlResult):
        with self.db.begin(write=True) as txn:
            value_bytes = value.model_dump_json().encode('utf-8')
            key_bytes = key.encode('utf-8')

            if len(value_bytes) > 2 ** 25:
                raise ValueError(
                    "Value too large to store in database", value_bytes)
                return
            txn.put(key_bytes, value_bytes)

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
                decoded_value = value.decode(
                    "utf-8")  # Convert bytes to string
                print(f"Key: {key}, Value: {decoded_value}")

    # Dump contents of the db in human readable format to "dump.txt"
    def dump_to_file(self):
        with self.db.begin() as txn:
            cursor = txn.cursor()

            with open("dump.txt", "w") as f:
                for key, value in cursor:
                    decoded_value = value.decode("utf-8")
                    f.write(f"Key: {key}\n\nValue: {decoded_value}\n\n\n")
