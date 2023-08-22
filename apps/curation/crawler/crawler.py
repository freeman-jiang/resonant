import asyncio

from .database import Database
from .root_urls import ROOT_URLS
from .worker import GlobalState, worker_main
from .link import Link


def add_root_urls(gs: GlobalState):
    for root in ROOT_URLS:
        gs.work_queue.put(
            Link(text=root["title"], url=root["url"], parent_url="root"))


async def main():
    global_state = GlobalState()
    add_root_urls(global_state)
    await worker_main(global_state)


if __name__ == "__main__":
    asyncio.run(main())
