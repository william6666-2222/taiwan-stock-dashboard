import logging
import time
import sys
import os

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import TAIWAN_50_STOCKS, LOOKBACK_DAYS

logger = logging.getLogger(__name__)


def fetch_ticker(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Fetch OHLCV for one ticker using Ticker.history() – cleaner output than yf.download()."""
    try:
        t  = yf.Ticker(ticker)
        df = t.history(start=start, end=end, auto_adjust=True)

        if df.empty:
            logger.warning(f"  ⚠ No data returned for {ticker}")
            return pd.DataFrame()

        df = df.reset_index()

        # Rename index column (could be 'Date', 'Datetime', 'Timestamp')
        for col in df.columns:
            if str(col).lower() in ('date', 'datetime', 'timestamp'):
                df = df.rename(columns={col: 'date'})
                break

        # Lowercase all columns
        df.columns = [str(c).lower() for c in df.columns]

        # Add ticker column explicitly
        df['ticker'] = ticker

        # Parse date
        df['date'] = pd.to_datetime(df['date']).dt.date

        # Keep only the columns we need
        keep = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
        available = [c for c in keep if c in df.columns]

        if 'ticker' not in available or 'close' not in available:
            logger.warning(f"  ⚠ Missing required columns for {ticker}: {df.columns.tolist()}")
            return pd.DataFrame()

        return df[available]

    except Exception as exc:
        logger.error(f"  ✗ Failed to fetch {ticker}: {exc}")
        return pd.DataFrame()


def extract_all(lookback_days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    end   = datetime.now()
    start = end - timedelta(days=lookback_days)

    logger.info(f"Extracting {len(TAIWAN_50_STOCKS)} tickers "
                f"from {start.date()} to {end.date()}…")

    frames = []
    for ticker in TAIWAN_50_STOCKS:
        logger.info(f"  → {ticker}")
        df = fetch_ticker(ticker, start, end)
        if not df.empty:
            frames.append(df)
        time.sleep(0.5)

    if not frames:
        raise RuntimeError("Extraction returned no data – check network / tickers.")

    combined = pd.concat(frames, ignore_index=True)

    # Final safety check
    if 'ticker' not in combined.columns:
        raise RuntimeError("'ticker' column missing after concat – check extract logic.")

    logger.info(f"Extracted {len(combined):,} rows from {len(frames)} tickers.")
    return combined
