import logging, time, sys, os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import TAIWAN_50_STOCKS, LOOKBACK_DAYS
logger = logging.getLogger(__name__)

def fetch_ticker(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True, actions=False)
        if df.empty:
            logger.warning(f"  ⚠ No data for {ticker}")
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df['ticker'] = ticker
        df['date'] = pd.to_datetime(df['date']).dt.date
        cols = [c for c in ['ticker','date','open','high','low','close','volume'] if c in df.columns]
        return df[cols]
    except Exception as exc:
        logger.error(f"  ✗ {ticker}: {exc}")
        return pd.DataFrame()

def extract_all(lookback_days=LOOKBACK_DAYS):
    end = datetime.now()
    start = end - timedelta(days=lookback_days)
    logger.info(f"Extracting {len(TAIWAN_50_STOCKS)} tickers…")
    frames = []
    for ticker in TAIWAN_50_STOCKS:
        logger.info(f"  → {ticker}")
        df = fetch_ticker(ticker, start, end)
        if not df.empty:
            frames.append(df)
        time.sleep(0.5)
    if not frames:
        raise RuntimeError("Extraction returned no data.")
    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"Extracted {len(combined):,} rows from {len(frames)} tickers.")
    return combined
