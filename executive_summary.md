# Taiwan 50 Stock Intelligence Dashboard ### Executive Summary
**Student:** [黃珽威 /B12303069 ]  
**Course:** [Data Visualization with Modern Data Science]  
**Deployment URL:** `https://taiwan-stock-dashboard-nw2yhx8kospgeczq9lerje.streamlit.app`  
**GitHub:** `https://github.com/william6666-2222/taiwan-stock-dashboard`

---

## Overview

This project builds and deploys a live stock market intelligence platform tracking 20 constituents of the TWSE Taiwan 50 Index (0050). The system ingests daily price data from Yahoo Finance, computes technical indicators through an automated ETL pipeline, persists results in a cloud database, and exposes four interactive analytical dashboards via a public Streamlit web application updated every weekday.

---

## System Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Data source | yfinance (Yahoo Finance API) | Daily OHLCV data for 20 Taiwan 50 stocks |
| ETL pipeline | Python — pandas, numpy | Extract → Transform → Load |
| Database | Supabase (PostgreSQL) | Cloud-persistent storage with RLS |
| Scheduler | GitHub Actions (cron) | Automated weekday pipeline trigger |
| Frontend | Streamlit + Plotly | Interactive dashboards |
| Deployment | Streamlit Cloud | Public URL, zero infrastructure management |

---

## Data Pipeline

The ETL pipeline runs automatically every **weekday at 4:00 PM Taiwan Time** (2.5 hours after TWSE close) via a scheduled GitHub Actions workflow. It proceeds in three stages:

**1. Extract** — For each of the 20 tickers, the pipeline calls `yfinance.Ticker.history()` to retrieve 365 days of OHLCV data. Results are normalised to a uniform schema and concatenated into a single DataFrame (~7,000 rows per run).

**2. Transform** — Four derived features are computed per ticker:
- `daily_return`: percentage change from previous close
- `ma20` / `ma60`: 20-day and 60-day simple moving averages
- `rsi`: 14-period Wilder's RSI using exponential smoothing
- `volatility`: 30-day rolling standard deviation annualised by × √252

Missing sessions caused by holidays are forward-filled up to 3 consecutive days to preserve continuity without introducing artificial data.

**3. Load** — Records are batch-upserted into Supabase using `ON CONFLICT (ticker, date)`, making the pipeline safely idempotent. Each successful run is logged to a `refresh_log` table, providing an audit trail visible in the dashboard sidebar.

---

## Dashboard Features

Four analytical views are accessible via the sidebar:

| Page | Key visualisations |
|------|-------------------|
| Market Overview | Treemap heatmap (volume-weighted, return-coloured), top-5 gainers/losers tables, cumulative return line chart |
| Stock Explorer | Candlestick chart with MA20/MA60 overlays, volume bar chart, RSI panel with overbought/oversold bands |
| Technical Signals | RSI scanner (alerts for RSI < 30 and > 70), MA crossover table (golden/death cross), risk–return scatter |
| Sector Analysis | Sector return bar chart, sector risk–return scatter, aggregated summary table |

---

## Key Design Decisions

**Supabase over local SQLite:** A hosted PostgreSQL database enables the public Streamlit Cloud deployment to query live data without bundling a local file. Row Level Security is enabled to allow anonymous reads while blocking writes from the frontend.

**GitHub Actions over manual refresh:** Automating the ETL via cron decouples data freshness from user actions — the dashboard always reflects the latest TWSE close without any manual intervention.

**yfinance over TWSE API:** Yahoo Finance provides a stable, free, and well-documented Python client for Taiwan stocks (`.TW` suffix), removing the need for TWSE authentication credentials.

---

## Conclusion

The result is a self-sustaining, end-to-end data product: a financial API feeds a cloud ETL pipeline that is automatically triggered daily and serves interactive dashboards at a public URL — demonstrating the full cycle from raw data ingestion to production deployment within a single Python ecosystem.
