from prisma.models import Page

Page.create_partial('NodePage', include=[
                    'id', 'outbound_urls', 'title', 'url'])
