from prisma import Prisma

from crawler.link import SUPPRESSED_DOMAINS


async def main():
    client = Prisma()

    await client.connect()

    processed = 0

    to_delete = []

    while True:
        pages = await client.page.find_many(take = 100, skip = processed)
        if len(pages) == 0:
            break
        print(f"Processing {len(pages)} pages")
        processed += len(pages)

        for p in pages:
            for suppressed in SUPPRESSED_DOMAINS:
                if suppressed in p.url:
                    to_delete.append(p.id)

    print("Deleting {} pages".format(len(to_delete)))
    if len(to_delete) > 0:
        await client.page.delete_many(where = {
            'id': {
                'in': to_delete
            }
        })

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())