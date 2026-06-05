import logging
import os
import math
from datetime import datetime, timezone

import pandas as pd
from supabase import create_client

logger = logging.getLogger(__name__)
BATCH_SIZE = 500

def _get_client():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set.")
    return create_client(url, key)

def _clean(v):
    """NaN / inf → None，讓 Supabase 存成 SQL NULL"""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v

def upsert(df: pd.DataFrame) -> int:
    client = _get_client()
    records = df.copy()
    records['date'] = records['date'].astype(str)

    # 每個欄位都過一遍 _clean，確保沒有 NaN
    data = [{k: _clean(v) for k, v in row.items()}
            for row in records.to_dict('records')]

    total = 0
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        (client.table('stock_daily')
               .upsert(batch, on_conflict='ticker,date')
               .execute())
        total += len(batch)
        logger.info(f"  Upserted {total:,} / {len(data):,} rows")

    try:
        (client.table('refresh_log')
               .insert({'refreshed_at': datetime.now(timezone.utc).isoformat(),
                        'rows_upserted': total, 'status': 'success'})
               .execute())
    except Exception as exc:
        logger.warning(f"refresh_log 寫入失敗（不影響資料）: {exc}")

    logger.info(f"Load complete: {total:,} rows upserted.")
    return total
