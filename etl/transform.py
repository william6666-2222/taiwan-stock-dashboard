import logging
import sys
import os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import (TAIWAN_50_STOCKS, MA_SHORT, MA_LONG,
                    RSI_PERIOD, VOLATILITY_WINDOW)

logger = logging.getLogger(__name__)

def _wilder_rsi(prices: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta    = prices.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).round(2)

def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(['ticker', 'date']).copy()

    # 1. Forward-fill holidays (up to 3 days) — FIX: use transform, not apply
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df.groupby('ticker')[col].transform(
            lambda x: x.ffill(limit=3)
        )
    df = df.dropna(subset=['close'])

    # 2. Daily return (%)
    df['daily_return'] = (
        df.groupby('ticker')['close']
          .pct_change()
          .mul(100)
          .round(4)
    )

    # 3. Moving averages
    for window, col in [(MA_SHORT, f'ma{MA_SHORT}'), (MA_LONG, f'ma{MA_LONG}')]:
        df[col] = (
            df.groupby('ticker')['close']
              .transform(lambda x: x.rolling(window, min_periods=1).mean())
              .round(2)
        )

    # 4. RSI (14-period Wilder's)
    df['rsi'] = df.groupby('ticker')['close'].transform(_wilder_rsi)

    # 5. Annualised rolling volatility
    df['volatility'] = (
        df.groupby('ticker')['daily_return']
          .transform(lambda x: x.rolling(VOLATILITY_WINDOW, min_periods=5)
                                .std()
                                .mul(np.sqrt(252)))
          .round(2)
    )

    # 6. Metadata
    df['name']   = df['ticker'].map(
        lambda t: TAIWAN_50_STOCKS.get(t, {}).get('name', t))
    df['sector'] = df['ticker'].map(
        lambda t: TAIWAN_50_STOCKS.get(t, {}).get('sector', 'Other'))

    logger.info(f"Transform complete: {len(df):,} rows, "
                f"{df['ticker'].nunique()} tickers, "
                f"{df['date'].min()} → {df['date'].max()}")
    return df
