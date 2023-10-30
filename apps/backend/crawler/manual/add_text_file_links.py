from crawler.link import Link
from crawler.prismac import PostgresClient

if __name__ == "__main__":
    pc = PostgresClient()

    pc.connect()

    links = []
    with open("total.txt", "rb") as f:
        for url in f.readlines():
            try:
                url = url.decode('ascii')
                l = Link.from_url(url)
                l.depth = 1
                l.text = "Curius"
            except ValueError:
                continue

            links.append(l)

    pc.add_tasks(links)