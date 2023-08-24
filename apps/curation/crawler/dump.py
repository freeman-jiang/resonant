from crawler.database import Database

db = Database("CrawlResult")

db.dump_to_file()
db.dump_json()
