import threading
from supabase import create_client, Client
from .config import settings

# one client per thread — the httpx connection pool inside the supabase
# client is not safe to share across threads (causes HTTP/2 ReadErrors on macOS)
_local = threading.local()


def get_db() -> Client:
    if not hasattr(_local, "client"):
        _local.client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _local.client
