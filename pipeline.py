#!/usr/bin/env python3
"""
Taiwan 50 Stock Intelligence – ETL Pipeline
============================================
Run manually:   python pipeline.py
Triggered by:   GitHub Actions (.github/workflows/daily_etl.yml)

Environment variables required:
    SUPABASE_URL   – your Supabase project URL
    SUPABASE_KEY   – your Supabase anon/service key
"""
import logging
import sys

from dotenv import load_dotenv
load_dotenv()  # Load .env file when running locally

from etl.extract   import extract_all
from etl.transform import transform
from etl.load      import upsert

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(name)s – %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('pipeline')


def main() -> None:
    logger.info("══════════════════════════════════════")
    logger.info("  Taiwan 50 ETL pipeline – START")
    logger.info("══════════════════════════════════════")

    try:
        # ── Step 1: Extract ──────────────────────────────────────────────────
        logger.info("[ 1/3 ] Extracting data from Yahoo Finance …")
        raw = extract_all()

        # ── Step 2: Transform ────────────────────────────────────────────────
        logger.info("[ 2/3 ] Transforming data …")
        cleaned = transform(raw)

        # ── Step 3: Load ─────────────────────────────────────────────────────
        logger.info("[ 3/3 ] Loading to Supabase …")
        count = upsert(cleaned)

        logger.info("══════════════════════════════════════")
        logger.info(f"  Pipeline COMPLETE  |  {count:,} rows upserted")
        logger.info("══════════════════════════════════════")

    except Exception as exc:
        logger.exception(f"Pipeline FAILED: {exc}")
        sys.exit(1)


if __name__ == '__main__':
    main()
