import functools
from supabase import create_client, Client
from .config import settings


@functools.lru_cache(maxsize=1)
def get_db() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)
