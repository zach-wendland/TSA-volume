from typing import List
from supabase import create_client, Client
from .models import VolumeRow
from .settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
from .utils import chunked

TABLE = "tsa_passenger_volumes"

def _client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Supabase env vars missing")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def upsert_rows(rows: List[VolumeRow]) -> int:
    if not rows:
        return 0
    sb = _client()
    # supabase-py v2 supports on_conflict
    total = 0
    payload = [r.model_dump() for r in rows]
    # chunk to avoid payload bloat
    for batch in chunked(payload, 1000):
        res = (
            sb.table(TABLE)
              .upsert(batch, on_conflict="date")  # unique on date
              .execute()
        )
        # res.data may include all rows; count by input
        total += len(batch)
    return total
