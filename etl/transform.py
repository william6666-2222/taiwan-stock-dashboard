"""
Step 2 – Transform
Clean raw OHLCV data and compute derived technical features:
  • daily_return   – percentage change from previous close
  • ma20 / ma60    – simple moving averages
  • rsi            – 14-period Wilder's RSI
  • volatility     – 30-day annualised rolling standard deviation
"""
import logging
import sys
import os

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import (TAIWAN_50_STOCKS, MA_SHORT, MA_LONG,
                    RSI_PERIOD, VOLATILITY_WINDOW)

logger = logging.getLogger(__name__)


# ── Helper functions ─────────────────────────────────────────────────────────

def _wilder_rsi(prices: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Wilder's smoothed RSI using exponential moving average."""
    delta     = prices.diff()
    gain      = delta.clip(lower=0)
    loss      = (-delta).clip(lower=0)
    avg_gain  = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss  = loss.ewm(com=period - 1, min_periods=period).mean()
    rs        = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).round(2)


# ── Main transform function ──────────────────────────────────────────────────

def transform(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply full transformation pipeline to raw OHLCV data.
    Input : DataFrame with columns [ticker, date, open, high, low, close, volume]
    Output: Same DataFrame + derived features + metadata columns
    """
    df = df.sort_values(['ticker', 'date']).copy()

    # ── 1. Handle missing sessions (holidays, circuit breaks) ────────────────
    #    Forward-fill up to 3 consecutive missing days per ticker
    df = (df
          .groupby('ticker', group_keys=False)
          .apply(lambda g: g.ffill(limit=3))
          .reset_index(drop=True))
    df = df.dropna(subset=['close'])

    # ── 2. Daily return (%) ───────────────────────────────────────────────────
    df['daily_return'] = (
        df.groupby('ticker')['close']
          .pct_change()
          .mul(100)
          .round(4)
    )

    # ── 3. Moving averages ────────────────────────────────────────────────────
    for window, col in [(MA_SHORT, f'ma{MA_SHORT}'), (MA_LONG, f'ma{MA_LONG}')]:
        df[col] = (
            df.groupby('ticker')['close']
              .transform(lambda x: x.rolling(window, min_periods=1).mean())
              .round(2)
        )

    # ── 4. Relative Strength Index (RSI 14) ───────────────────────────────────
    df['rsi'] = df.groupby('ticker')['close'].transform(_wilder_rsi)

    # ── 5. Annualised rolling volatility ─────────────────────────────────────
    #    σ_annual = σ_daily × √252
    df['volatility'] = (
        df.groupby('ticker')['daily_return']
          .transform(lambda x: x.rolling(VOLATILITY_WINDOW, min_periods=5)
                                .std()
                                .mul(np.sqrt(252)))
          .round(2)
    )

    # ── 6. Attach metadata from config ───────────────────────────────────────
    df['name']   = df['ticker'].map(lambda t: TAIWAN_50_STOCKS.get(t, {}).get('name',   t))
    df['sector'] = df['ticker'].map(lambda t: TAIWAN_50_STOCKS.get(t, {}).get('sector', 'Other'))

    logger.info(f"Transform complete: {len(df):,} rows, "
                f"{df['ticker'].nunique()} tickers, "
                f"{df['date'].min()} → {df['date'].max()}")
    return df
