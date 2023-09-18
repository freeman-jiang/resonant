import asyncio
from dotenv import load_dotenv

from prisma import Prisma
from prisma.enums import TaskStatus

# This script is used to set all CrawlTasks that are currently in a PROCESSING state to PENDING
# This is useful if a worker process crashed or was cancelled (by CTRL+C for instance) and the crawl
# was never completed


async def main():
    load_dotenv()
    db = Prisma()
    await db.connect()

    tasks_updated = await db.crawltask.update_many(
        data={
            "status":  TaskStatus.PENDING
        },
        where={
            "status": TaskStatus.PROCESSING
        }
    )

    print(f"Updated {tasks_updated} tasks from PROCESSING to PENDING")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
