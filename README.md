# 🇹🇼 Taiwan 50 Stock Intelligence Dashboard

A full-stack stock market dashboard tracking the 20 largest constituents of the TWSE Taiwan 50 Index (0050).  
Built with Streamlit · Plotly · Supabase · GitHub Actions.

---

## Setup Guide (5 steps, ~20 minutes)

### Step 1 — Supabase database

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project (any name, any region)
3. Go to **SQL Editor** and paste the entire contents of `supabase_setup.sql`
4. Click **Run** — this creates the `stock_daily` and `refresh_log` tables
5. Go to **Project Settings → API** and copy:
   - **Project URL** (e.g. `https://xxxx.supabase.co`)
   - **anon public key**

### Step 2 — Local environment

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/taiwan-stock-dashboard.git
cd taiwan-stock-dashboard

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Open .env and paste your SUPABASE_URL and SUPABASE_KEY
```

### Step 3 — Populate the database (first run)

```bash
python pipeline.py
```

This fetches 365 days of data for all 20 stocks and loads it into Supabase (~2–3 minutes).

### Step 4 — Run the dashboard locally

```bash
# Create Streamlit secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Open secrets.toml and paste the same SUPABASE_URL and SUPABASE_KEY

streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Step 5 — Deploy to Streamlit Cloud

1. Push your code to a **public** GitHub repository
   - Make sure `.streamlit/secrets.toml` and `.env` are in `.gitignore` (they are by default)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. Click **Advanced settings** → add your secrets:
   ```
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```
5. Click **Deploy** — you'll get a public URL in ~2 minutes

### Step 6 — Set up automated daily refresh

1. In your GitHub repo, go to **Settings → Secrets and variables → Actions**
2. Add two repository secrets:
   - `SUPABASE_URL` = your Supabase project URL
   - `SUPABASE_KEY` = your Supabase anon key
3. The workflow in `.github/workflows/daily_etl.yml` will now run automatically every weekday at 4:00 PM Taiwan Time
4. You can also trigger it manually via **Actions → Daily Stock ETL → Run workflow**

---

## Project Structure

```
taiwan-stock-dashboard/
├── app.py                          # Streamlit dashboard (4 pages)
├── pipeline.py                     # ETL orchestrator
├── config.py                       # Stock list + indicator parameters
├── etl/
│   ├── extract.py                  # Step 1: fetch from yfinance
│   ├── transform.py                # Step 2: compute MA, RSI, volatility
│   └── load.py                     # Step 3: upsert to Supabase
├── .github/workflows/
│   └── daily_etl.yml               # Automated daily cron job
├── supabase_setup.sql              # Run once in Supabase SQL Editor
├── requirements.txt
├── .env.example                    # Template for local secrets
├── .streamlit/secrets.toml.example # Template for Streamlit secrets
└── executive_summary.md
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No data in database` | Run `python pipeline.py` first |
| `EnvironmentError: SUPABASE_URL not set` | Check your `.env` file or GitHub secrets |
| yfinance returns empty DataFrame | Some tickers may be temporarily unavailable; re-run |
| Streamlit Cloud can't read data | Check **App settings → Secrets** are set correctly |
