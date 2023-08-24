
import os
from supabase import create_client, Client


class Supabase:
    client: Client

    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        self.client = create_client(url, key)
