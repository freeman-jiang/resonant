import os

from prisma import Prisma

from crawler.prismac import PostgresClient
import dotenv
dotenv.load_dotenv()

client = Prisma(datasource={'url': os.environ['DATABASE_URL_SUPABASE']})
db = PostgresClient(None)

async def main():
    db.connect()
    await client.connect()
    messages = await client.message.find_many()

    to_delete = []

    for m in messages:
        if m.page_id is not None:
            if db.get_page(id = m.page_id) is None:
                print("MESSAGE BAD", m)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())