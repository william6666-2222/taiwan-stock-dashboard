-- ============================================================
-- Taiwan 50 Stock Dashboard – Supabase setup
-- Run this once in the Supabase SQL Editor before first use
-- ============================================================

-- ── Table 1: Daily stock data ─────────────────────────────
CREATE TABLE IF NOT EXISTS stock_daily (
    id            BIGSERIAL    PRIMARY KEY,
    ticker        VARCHAR(10)  NOT NULL,
    date          DATE         NOT NULL,
    open          NUMERIC(10,2),
    high          NUMERIC(10,2),
    low           NUMERIC(10,2),
    close         NUMERIC(10,2),
    volume        BIGINT,
    daily_return  NUMERIC(8,4),
    ma20          NUMERIC(10,2),
    ma60          NUMERIC(10,2),
    rsi           NUMERIC(6,2),
    volatility    NUMERIC(8,4),
    name          VARCHAR(100),
    sector        VARCHAR(50),
    created_at    TIMESTAMPTZ  DEFAULT NOW(),

    -- Prevents duplicate rows on re-run; required for upsert ON CONFLICT
    UNIQUE (ticker, date)
);

-- Public read access (Streamlit app reads without authentication)
ALTER TABLE stock_daily ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read" ON stock_daily
    FOR SELECT USING (true);

-- ── Table 2: Pipeline refresh log ────────────────────────
CREATE TABLE IF NOT EXISTS refresh_log (
    id            BIGSERIAL    PRIMARY KEY,
    refreshed_at  TIMESTAMPTZ  NOT NULL,
    rows_upserted INT,
    status        VARCHAR(20)
);

ALTER TABLE refresh_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read" ON refresh_log
    FOR SELECT USING (true);

-- ── Optional: Speed up common dashboard queries ───────────
CREATE INDEX IF NOT EXISTS idx_stock_daily_ticker_date
    ON stock_daily (ticker, date DESC);

CREATE INDEX IF NOT EXISTS idx_stock_daily_date
    ON stock_daily (date DESC);

-- ── Verify setup ──────────────────────────────────────────
SELECT 'Setup complete! Tables ready.' AS status;
