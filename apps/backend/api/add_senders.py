from collections import defaultdict

from prisma import Prisma

from api.page_response import Sender, PageResponse


async def get_senders_for_pages(client: Prisma, page_ids: list[int]) -> dict[int, list[Sender]]:
    messages = await client.message.find_many(
        order={'sent_on': 'desc'},
        include={'sender': True},
        where={
            'page_id': {
                'in': page_ids
            }
        })

    sender_map = defaultdict(list)

    for m in messages:
        sender = Sender.from_message(m)
        sender_map[m.page_id].append(sender)

    return sender_map
async def add_senders(client: Prisma, pages: list[PageResponse]):
    senders = await get_senders_for_pages(client, [p.id for p in pages])

    for p in pages:
        p.senders = senders[p.id]
