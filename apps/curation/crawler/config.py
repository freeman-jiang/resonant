import argparse

DEFAULT_MAX_LINKS_TO_CRAWL = 20000
DEFAULT_WORKERS = 10
DEFAULT_DEBUG_WORKERS = 1
DEFAULT_MAX_QUEUE_SIZE = 500  # maximum number of tasks to keep in the queue at once
DEFAULT_MAX_CRAWL_DEPTH = 2


class Config():
    should_debug: bool
    max_links: int
    num_workers: int
    max_queue_size: int
    max_crawl_depth: int

    def __init__(self):
        parser = argparse.ArgumentParser(prog="python3 -m crawler.main")
        parser.add_argument("--max_links", type=int,
                            help="The maximum number of links to crawl", default=DEFAULT_MAX_LINKS_TO_CRAWL)
        parser.add_argument("--debug", action="store_true",
                            help="Runs the crawler with a single worker, slowly", default=False)
        max_links = parser.parse_args().max_links
        should_debug = parser.parse_args().debug

        self.should_debug = should_debug
        self.max_links = max_links
        self.num_workers = DEFAULT_DEBUG_WORKERS if should_debug else DEFAULT_WORKERS
        self.max_queue_size = DEFAULT_MAX_QUEUE_SIZE
        self.max_crawl_depth = DEFAULT_MAX_CRAWL_DEPTH
